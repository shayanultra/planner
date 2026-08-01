"""Raster2Seq inference adapter — primary geometry only (no Grok/Cosmos)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np

from services.raster2seq_adapter.checkpoint import (
    CUBICASA5K_ALIAS,
    DEFAULT_REPO,
    load_local_config,
    resolve_local_checkpoint,
)
from services.raster2seq_adapter.errors import Raster2SeqRuntimeError
from services.raster2seq_adapter.map_output import (
    PolygonItem,
    apply_polish_to_items,
    map_generate_output,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_R2S_ROOT = _REPO_ROOT / "Raster2Seq"


@dataclass(frozen=True)
class PolygonSequenceResult:
    polygons: list[PolygonItem]
    checkpoint_alias: str
    checkpoint_path: str
    checkpoint_repo: str
    image_size: int
    polish_applied: bool
    source_content_sha256: str | None


def _ensure_r2s_on_path() -> None:
    root = str(_R2S_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def _select_device() -> str:
    import torch

    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def _build_args_from_config(cfg: dict[str, Any], checkpoint_path: Path) -> SimpleNamespace:
    inf = dict(cfg.get("inference_args") or {})
    # Defaults aligned with predict.py + cubicasa5k config.json
    ns = SimpleNamespace(
        batch_size=1,
        debug=False,
        input_channels=int(inf.get("input_channels", 3)),
        image_norm=False,
        image_size=int(inf.get("image_size", 256)),
        ema4eval=bool(inf.get("ema4eval", True)),
        measure_time=False,
        disable_sampling_cache=False,
        use_anchor=bool(inf.get("use_anchor", True)),
        drop_wd=False,
        plot_text=False,
        image_scale=2,
        one_color=False,
        crop_white_space=False,
        refinement=False,
        refinement_threshold=0.5,
        poly2seq=bool(inf.get("poly2seq", True)),
        seq_len=int(inf.get("seq_len", 512)),
        num_bins=int(inf.get("num_bins", 32)),
        pre_decoder_pos_embed=False,
        learnable_dec_pe=False,
        dec_qkv_proj=False,
        dec_attn_concat_src=bool(inf.get("dec_attn_concat_src", True)),
        per_token_sem_loss=bool(inf.get("per_token_sem_loss", True)),
        add_cls_token=False,
        backbone="resnet50",
        lr_backbone=0.0,
        dilation=False,
        position_embedding="sine",
        semantic_classes=int(inf.get("semantic_classes", 12)),
        disable_poly_refine=bool(inf.get("disable_poly_refine", True)),
        dataset_name=str(inf.get("dataset_name", "cubicasa")),
        device=_select_device(),
        seed=42,
        checkpoint=str(checkpoint_path),
        num_workers=0,
        hidden_dim=256,
        nheads=8,
        enc_layers=6,
        dec_layers=6,
        dim_feedforward=1024,
        dropout=0.0,
        num_feature_levels=4,
        dec_n_points=4,
        enc_n_points=4,
        num_queries=800,
        aux_loss=False,
        with_box_refine=False,
        two_stage=False,
        frozen_weights=None,
        masks=False,
        # roomformer / misc flags often required by build_model
        room_cls=True,
    )
    return ns


def _rgb_to_model_tensor(rgb: np.ndarray, image_size: int, input_channels: int):
    """Match predict.ImageDataset preprocessing as closely as practical."""
    import torch
    from PIL import Image

    _ensure_r2s_on_path()
    try:
        from detectron2.data import transforms as T
        from datasets.transforms import ResizeAndPad
    except Exception as exc:  # noqa: BLE001 — surface as runtime
        raise Raster2SeqRuntimeError(
            "Failed to import Raster2Seq/Detectron2 transforms. "
            f"Install Raster2Seq deps (detectron2, pycocotools, fvcore). Detail: {exc}"
        ) from exc

    if rgb.dtype != np.uint8 or rgb.ndim != 3 or rgb.shape[2] != 3:
        raise Raster2SeqRuntimeError(
            f"Expected HxWx3 uint8 RGB, got shape={getattr(rgb, 'shape', None)} dtype={getattr(rgb, 'dtype', None)}"
        )

    image = np.array(Image.fromarray(rgb, mode="RGB"))
    if input_channels == 1:
        image = np.array(Image.fromarray(rgb, mode="RGB").convert("L"))

    data_transform = T.AugmentationList(
        [ResizeAndPad((image_size, image_size), pad_value=255)]
    )
    aug_input = T.AugInput(image if input_channels != 1 else np.stack([image] * 3, axis=-1))
    _ = data_transform(aug_input)
    image = aug_input.image
    if len(image.shape) == 2:
        exp = np.expand_dims(image, 0)
    else:
        exp = image.transpose((2, 0, 1))
    tensor = (1 / 255) * torch.as_tensor(np.array(exp), dtype=torch.float32)
    return tensor.unsqueeze(0)  # BCHW


def _load_model(args: SimpleNamespace):
    import copy

    import torch

    _ensure_r2s_on_path()
    try:
        from datasets.discrete_tokenizer import DiscreteTokenizer
        from engine import generate
        from models import build_model
        from raster2seq_hub import resolve_checkpoint_path
    except Exception as exc:  # noqa: BLE001
        raise Raster2SeqRuntimeError(
            "Failed to import vendored Raster2Seq (models/engine). "
            "Build MultiScaleDeformableAttention ops and install detectron2. "
            f"Detail: {exc}"
        ) from exc

    tokenizer = None
    if args.poly2seq:
        tokenizer = DiscreteTokenizer(args.num_bins, args.seq_len, add_cls=args.add_cls_token)
        args.vocab_size = len(tokenizer)

    try:
        model = build_model(args, train=False, tokenizer=tokenizer)
    except Exception as exc:  # noqa: BLE001
        raise Raster2SeqRuntimeError(
            f"build_model failed (often missing CUDA deformable-attention ops on Mac): {exc}"
        ) from exc

    device = torch.device(args.device)
    try:
        model.to(device)
    except Exception:
        # MPS edge cases → CPU
        args.device = "cpu"
        device = torch.device("cpu")
        model.to(device)

    ckpt_path = resolve_checkpoint_path(args.checkpoint)
    checkpoint = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    if args.ema4eval and "ema" in checkpoint:
        ckpt_state_dict = copy.deepcopy(checkpoint["ema"])
    else:
        ckpt_state_dict = copy.deepcopy(checkpoint["model"])
    for key in list(ckpt_state_dict.keys()):
        if key.startswith("module."):
            ckpt_state_dict[key[7:]] = ckpt_state_dict.pop(key)
    model.load_state_dict(ckpt_state_dict, strict=False)
    for param in model.parameters():
        param.requires_grad = False
    model.eval()
    return model, generate, device


def infer_polygons(
    source: Any,
    *,
    polish: bool = False,
    polish_tolerance: float = 1.0,
    checkpoint_alias: str = CUBICASA5K_ALIAS,
    checkpoint_path: str | Path | None = None,
    _generate_fn=None,
    _model=None,
) -> PolygonSequenceResult:
    """Run Raster2Seq on a NormalizedRaster or image path; return Polygon Sequence.

    ``polish`` applies Douglas-Peucker **after** model output only (default off).
    Does not call Grok or Cosmos for geometry.
    """
    from services.floorplan_input import NormalizedRaster, normalize_floorplan_input

    if isinstance(source, NormalizedRaster):
        raster = source
    else:
        raster = normalize_floorplan_input(source)

    ckpt = resolve_local_checkpoint(checkpoint_alias, path=checkpoint_path)
    cfg = load_local_config(ckpt)
    args = _build_args_from_config(cfg, ckpt)

    # Allow tests to inject generate without loading weights
    if _generate_fn is not None:
        # Minimal fake path: pass through canned generate output via rgb ignored
        gen_out = _generate_fn(raster.rgb)
        items = map_generate_output(gen_out)
        items = apply_polish_to_items(items, enabled=polish, tolerance=polish_tolerance)
        return PolygonSequenceResult(
            polygons=items,
            checkpoint_alias=checkpoint_alias,
            checkpoint_path=str(ckpt),
            checkpoint_repo=DEFAULT_REPO,
            image_size=args.image_size,
            polish_applied=polish,
            source_content_sha256=raster.content_sha256,
        )

    model, generate, device = _load_model(args) if _model is None else (_model[0], _model[1], _model[2])
    tensor = _rgb_to_model_tensor(raster.rgb, args.image_size, args.input_channels)
    tensor = tensor.to(device)
    try:
        gen_out = generate(
            model,
            tensor,
            semantic_rich=args.semantic_classes > 0,
            use_cache=True,
            per_token_sem_loss=args.per_token_sem_loss,
            drop_wd=args.drop_wd,
            poly2seq=args.poly2seq,
        )
    except Exception as exc:  # noqa: BLE001
        raise Raster2SeqRuntimeError(f"Raster2Seq generate failed: {exc}") from exc

    label_map = None
    try:
        _ensure_r2s_on_path()
        from util.plot_utils import CC5K_LABEL

        if isinstance(CC5K_LABEL, dict):
            label_map = {int(k): str(v) for k, v in CC5K_LABEL.items()}
        elif isinstance(CC5K_LABEL, (list, tuple)):
            label_map = {i: str(v) for i, v in enumerate(CC5K_LABEL)}
    except Exception:
        label_map = None

    items = map_generate_output(gen_out, label_map=label_map)
    items = apply_polish_to_items(items, enabled=polish, tolerance=polish_tolerance)
    return PolygonSequenceResult(
        polygons=items,
        checkpoint_alias=checkpoint_alias,
        checkpoint_path=str(ckpt),
        checkpoint_repo=DEFAULT_REPO,
        image_size=args.image_size,
        polish_applied=polish,
        source_content_sha256=raster.content_sha256,
    )
