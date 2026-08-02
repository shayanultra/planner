- Do not preserve backward compatibility.
- Choose the simplest implementation that fully meets the current requirements.
- Prefer established, well-maintained libraries over custom implementation.

## Agent skills

### Issue tracker

Issues live as local markdown under `.scratch/<feature>/`. See `docs/agents/issue-tracker.md`.

### Triage labels

Default five-role vocabulary (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout (`CONTEXT.md` + `docs/adr/` at repo root). See `docs/agents/domain.md`.

## Browser Automation

Use `agent-browser` for web automation. Run `agent-browser --help` for all commands.

Core workflow:

1. `agent-browser open <url>` - Navigate to page
2. `agent-browser snapshot -i` - Get interactive elements with refs (@e1, @e2)
3. `agent-browser click @e1` / `fill @e2 "text"` - Interact using refs
4. Re-snapshot after page changes

<!-- OPENWIKI:START -->

## OpenWiki

This repository uses OpenWiki for recurring code documentation. Start with `openwiki/quickstart.md`, then follow its links to architecture, workflows, domain concepts, operations, integrations, testing guidance, and source maps.

The scheduled OpenWiki GitHub Actions workflow refreshes the repository wiki. Do not hand-edit generated OpenWiki pages unless explicitly asked; prefer updating source code/docs and letting OpenWiki regenerate.

<!-- OPENWIKI:END -->

## Operational Component Registry

### Document control

| Field | Value |
|-------|--------|
| Document ID | OCR-PLANNER-AI-v3 |
| Title | Operational Component Registry — System Component Allocation |
| Alignment | NASA/SP-2016-6105 Rev2 (Systems Engineering Handbook): §4 Logical Decomposition / Design Solution; §6.3 Interface Management; **§6.4 Technical Risk Management** |
| Architecture authority | `docs/goal.md` (sole) |
| Handbook extract | `docs/nasa-sp-2016.md` |
| Effective date | 2026-08-02 |
| Scope | Every agent runtime, autonomous background loop, and specialist tool plane **found in the workspace or required by goal.md** |

### Purpose (NASA SE framing)

This registry allocates **functions** (stakeholder goals and task sequences from `docs/goal.md`) to **components** with explicit **system boundaries**, **interface control contracts (ICDs)**, **resource bounds**, and **degraded-mode / fault isolation protocols** (NASA §6.4 risk triplets: scenario → likelihood/consequence mitigation → residual control).

**Status legend**

| Status | Meaning |
|--------|---------|
| **AS-BUILT** | Implemented in Planner AI Python services / schema and under test |
| **PARTIAL** | Schema or tree present; product integration incomplete |
| **REQUIRED-NOT-BUILT** | Mandated by `docs/goal.md`; ICD specified here for implementation |

**Global allocation law (non-negotiable from goal.md)**

1. Floorplan geometry authority: **Raster2Seq only** (no Grok/Cosmos/classical CV as primary geometry).
2. **Single-process C++ agent loop** is the primary orchestration path for Extreme Token Efficiency (ETE).
3. **Controlled parallel tool calls** inside that loop are allowed; **full multi-agent graphs are not** on the high-volume critical path.
4. **High-volume autonomous loops never touch the Portal** (Open WebUI).
5. 2D Layout polygons are authoritative; 3D is deterministic extrusion of verified 2D only.

---

### Inventory summary

| Component ID | Status | Runtime locus |
|--------------|--------|---------------|
| OCR-01-CPP-AGENT-LOOP | REQUIRED-NOT-BUILT (Phase 3) | llama.cpp + agent-loop extensions (single process) |
| OCR-02-PORTAL-OPENWEBUI | PARTIAL (vendored; Phase 5 wiring incomplete) | Open WebUI SvelteKit |
| OCR-03-TS1-RECONSTRUCTION | AS-BUILT (Slice A composition) | Python tool plane |
| OCR-03a-INPUT-NORMALIZE | AS-BUILT | `services/floorplan_input` |
| OCR-03b-R2S-INFER | AS-BUILT unit path; live env gated | `services/raster2seq_adapter` + `Raster2Seq/` |
| OCR-03c-LAYOUT-BUILD-PERSIST | AS-BUILT | `services/layout_builder` → Postgres |
| OCR-04-TS2-OPTIMIZE-KITCHEN | REQUIRED-NOT-BUILT | C++ tool + optimizer sidecars |
| OCR-05-DATA-PLANE | AS-BUILT schema (Phase 1) | Postgres/Neon + pgvector |
| OCR-06-INTEL-GROK | REQUIRED-NOT-BUILT | External xAI OpenAI-compatible API |
| OCR-07-INTEL-COSMOS | REQUIRED-NOT-BUILT (synthesis only) | Cosmos 3 Nano / 4-Step |
| OCR-08-VIEWER-2D3D | REQUIRED-NOT-BUILT | Konva 2D + Three.js / openPlan3D |
| OCR-09-MCP-TOOL-SURFACE | REQUIRED-NOT-BUILT | MCP / OpenAI tools between C++ and Python |
| OCR-10-AUTONOMOUS-BG-LOOP | REQUIRED-NOT-BUILT | C++-only high-volume iteration loop |
| OCR-11-AUDIT-OBS | PARTIAL | `audit_log` AS-BUILT; OTel stack Phase 7 |

---

## OCR-01-CPP-AGENT-LOOP

### 1. Component ID & system boundary

| Field | Specification |
|-------|----------------|
| **Component ID** | OCR-01-CPP-AGENT-LOOP |
| **Name** | Primary C++ Agent Runtime Loop |
| **Status** | REQUIRED-NOT-BUILT as productized Planner AI loop (vendored trees: `llama.cpp/`, `llama-agent/`, `chatllm.cpp/` present for integration) |
| **Runtime locus** | Single OS process: **llama.cpp** server/core + agent-loop extensions (llama-agent / chatllm.cpp style) |
| **System boundary** | **Inside** Agent Runtime Layer; **outside** Portal. Consumes tools via OCR-09; never embeds Open WebUI request path for high-volume work |
| **Concurrency model** | One primary sequential reasoning loop; **controlled parallel tool calls** only (goal §3.3) |

### 2. Stakeholder policy allocation (`docs/goal.md`)

| Policy element | Allocation |
|----------------|------------|
| Goal: Extreme Token Efficiency + Commoditized Pricing on high-volume loops | **Primary owner** — single-process loop mandatory |
| Goal: complete user flow with deterministic floorplan accuracy | Routes TS1 to OCR-03 via tools; does not invent geometry |
| Goal: kitchen system generation | Routes TS2 to OCR-04 after Layout exists |
| Success: token/cost reduction vs naïve multi-hop | Enforced by single loop + caching + GBNF (Phase 6) |
| Routing rule: interactive chat/planning/refinement | May call OCR-06 (Grok-4.5) |
| Routing rule: floorplan reconstruction | **Must** call OCR-03 / Raster2Seq path only |
| Routing rule: one-shot synthesis | May call OCR-07 after placement locked |
| Phase 3 – C++ Agent Runtime | Entire phase |
| Phase 6 – Efficiency Mechanisms | Quantization, KV/prefix cache, GBNF, parallel tools, portal bypass |
| Non-goal: multi-agent critical path | **Reject** multi-agent graphs on high-volume TS1/TS2 |

### 3. Interface control contracts

**Inbound (from Portal OCR-02 or autonomous scheduler OCR-10)**

```json
{
  "type": "agent_turn_request",
  "session_id": "uuid",
  "messages": [{"role": "user|assistant|tool", "content": "string"}],
  "tools_enabled": ["parse_and_map_floorplan", "optimize_kitchen"],
  "mode": "interactive|autonomous",
  "constraints": {
    "max_tool_rounds": "integer >= 1",
    "forbid_portal_callbacks": true
  }
}
```

**Outbound tool call (to OCR-09)**

```json
{
  "type": "tool_call",
  "id": "string",
  "name": "parse_and_map_floorplan|optimize_kitchen",
  "arguments": {}
}
```

**Outbound assistant message (OpenAI-compatible)**

```json
{
  "id": "string",
  "object": "chat.completion",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "string",
      "tool_calls": []
    }
  }]
}
```

**C++ conceptual structs (ICD for implementation)**

```cpp
// REQUIRED-NOT-BUILT — field contract for Phase 3
struct AgentTurnRequest {
  std::string session_id;
  std::vector<ChatMessage> messages;
  std::vector<std::string> tools_enabled;
  enum class Mode { Interactive, Autonomous } mode;
  int max_tool_rounds;
  bool forbid_portal_callbacks; // must be true for OCR-10
};

struct ToolCall {
  std::string id;
  std::string name;
  std::string arguments_json;
};
```

**GBNF / constrained decoding:** catalog SKU and size tokens only (goal Phase 3/6) — grammar artifacts live with runtime, not Portal.

### 4. Resource bounds & efficiency gains

| Bound | Value / rule |
|-------|----------------|
| Process model | **Exactly one** primary agent process for high-volume work |
| Context window (Phase 3 example) | `llama-server -c 8192` baseline; raise only with measured KV cost |
| Quantization | Q4_K_M or Q5_K_M (Phase 6) |
| Caching | Prefix/KV cache of **layout JSON + catalog context** across iterations |
| Token efficiency target | ~**50% fewer steps**, ~**4× fewer output tokens** vs naïve multi-hop multi-agent baselines |
| Parallelism | Tool-level only (e.g., parallel catalog retrieval + scoring); not multi-agent debate |
| Portal coupling | **Zero** for OCR-10 autonomous jobs |
| Geometry generation by LLM | **Forbidden** |

### 5. Degradation & fault isolation (NASA §6.4)

| Scenario | Detection | Deterministic response | Residual risk control |
|----------|-----------|------------------------|---------------------|
| Tool OCR-03/04 timeout | Wall-clock tool deadline | Return tool error to loop; do not invent Layout; log OCR-11 | Retry budget N≤2 then fail turn |
| Tool returns invalid JSON | Schema validation | Reject payload; no DB write from C++ | Force re-call or abort |
| Multi-agent orchestration requested on critical path | Mode/policy gate | **Refuse**; stay single-process | Audit `route=forbidden_multi_agent` |
| Grok (OCR-06) unavailable | HTTP/API error | Degrade interactive planning; **TS1 still available** via tools | User-visible degraded mode |
| Cosmos (OCR-07) unavailable | API/model error | Skip synthesis; keep deterministic placement | No geometry impact |
| KV/cache corruption | Checksum / load fail | Cold start context; rebuild prefix from Postgres Layout | Session continuity loss only |
| Safety: attempt to mutate geometry without Raster2Seq | Tool name / route check | **Hard block** | Audit + alert |

---

## OCR-02-PORTAL-OPENWEBUI

### 1. Component ID & system boundary

| Field | Specification |
|-------|----------------|
| **Component ID** | OCR-02-PORTAL-OPENWEBUI |
| **Name** | User-Facing Portal |
| **Status** | PARTIAL — tree `open-webui/` vendored; Planner AI custom viewer/MCP wiring **not** complete |
| **Runtime locus** | **Open WebUI (SvelteKit)** browser + Node/Python backend as shipped by upstream |
| **System boundary** | User-facing plane only. Talks to OCR-01 via OpenAI-compatible HTTP + MCP. **Must not** host high-volume autonomous reconstruction loops |

### 2. Stakeholder policy allocation

| Policy | Allocation |
|--------|------------|
| User flow: upload floorplan, view 2D/3D, select finishes, inspiration | Portal UX surface |
| Phase 5 – Portal | Owner |
| Phase 2 viewer integration note | Host OCR-08 component |
| Autonomous loops never touch portal | **Negative allocation** — OCR-10 must not call Portal APIs |
| Success: user engagement metrics | Observability consumer |

### 3. Interface control contracts

**Outbound to OCR-01 (OpenAI-compatible)**

```http
POST {AGENT_BASE}/v1/chat/completions
Content-Type: application/json

{
  "model": "string",
  "messages": [{"role": "user", "content": "string | multimodal parts"}],
  "tools": [/* MCP-exported tools */],
  "stream": true
}
```

**Inbound Layout display (from Postgres via backend or tool result)**

```json
{
  "layout_id": "uuid",
  "svg": "<svg>...</svg>",
  "extrusion": { "wall_height_m": 2.7, "nodes": [] },
  "geometry_fingerprint": "sha256-hex"
}
```

**Environment (Phase 5)**

- `OPENAI_API_BASE_URL` → OCR-01  
- MCP tools enabled  
- Custom viewer component for SVG + Three.js (OCR-08)

### 4. Resource bounds & efficiency gains

| Bound | Rule |
|-------|------|
| Role in ETE | **Not** on high-volume path; thin interactive client |
| Payload | Prefer layout_id + fetch over re-running reconstruction |
| 3D assets | GLB via CDN URLs in scene state (goal §3.1); InstancedMesh for repeated SKUs |
| Compile | Thin, multi-backend Open WebUI configuration |

### 5. Degradation & fault isolation (NASA §6.4)

| Scenario | Response |
|----------|----------|
| Agent runtime down | Show connection error; **do not** run Raster2Seq in browser |
| Stale layout | Re-fetch by `layout_id`; fingerprint mismatch → force refresh |
| Viewer crash | Keep 2D SVG fallback; 3D optional |
| User edits 2D (future) | Must write back to Layout authority in Postgres — never only local Three.js mesh |
| Autonomous job mis-routed to Portal | Reject / redirect to OCR-10 |

---

## OCR-03-TS1-RECONSTRUCTION

### 1. Component ID & system boundary

| Field | Specification |
|-------|----------------|
| **Component ID** | OCR-03-TS1-RECONSTRUCTION |
| **Name** | Task Sequence 1 — `parse_and_map_floorplan` public composition |
| **Status** | **AS-BUILT** |
| **Runtime locus** | Python process / library: `services/parse_and_map` |
| **System boundary** | Data & Tool Plane specialist. Invoked by OCR-09/OCR-01; **not** by Portal directly for autonomous volume |
| **Subcomponents** | OCR-03a, OCR-03b, OCR-03c (strict sequential pipeline) |

### 2. Stakeholder policy allocation

| Policy | Allocation |
|--------|------------|
| **Task Sequence 1 — `parse_and_map_floorplan`** | **Sole functional owner** of end-to-end reconstruction composition |
| Goal: multi-modal → identical accurate 2D+3D | Owner of pipeline determinism (fingerprint) |
| Success: ≥98% geometric fidelity | Depends on OCR-03b checkpoint quality; composition preserves polygons |
| Routing: reconstruction → Raster2Seq | Enforced: default infer is Raster2Seq only |
| Phase 2 – Floorplan Reconstruction Service | Primary as-built realization |
| Slice A acceptance 1–6 | Satisfied on unit path (see `docs/session/2026-08-01-slice-a-gates.md`) |

### 3. Interface control contracts

**Public function (AS-BUILT)** — `services/parse_and_map/seam.py`:

```python
def parse_and_map_floorplan(
    input_path: str | Path,
    *,
    conn: Any | None = None,
    infer_fn: Callable[..., PolygonSequenceResult] | None = None,
    polish: bool = False,
    polish_tolerance: float = 1.0,
    scale_meters_per_unit: float | None = None,
    scale_user_confirmed: bool = False,
    wall_height_m: float = 2.7,
    source_kind: str | None = None,
    close_conn: bool | None = None,
) -> LayoutRow
```

**Composition sequence (mandatory order)**

1. `normalize_floorplan_input(path)` → `NormalizedRaster`  
2. `infer_fn or infer_polygons(normalized, polish=...)` → `PolygonSequenceResult`  
3. `build_and_persist_layout(...)` → `LayoutRow` + `audit_log`

**Output `LayoutRow` (AS-BUILT)**

```python
@dataclass(frozen=True)
class LayoutRow:
    id: UUID
    geometry: dict[str, Any]
    svg: str
    extrusion: dict[str, Any]
    geometry_fingerprint: str
    source_kind: str  # image | pdf | text
    content_sha256: str | None
    scale_meters_per_unit: float | None
    scale_user_confirmed: bool
    audit_id: int | None = None
```

**MCP tool schema (REQUIRED for OCR-09 — not yet registered)**

```json
{
  "name": "parse_and_map_floorplan",
  "description": "Normalize floorplan image/PDF, run Raster2Seq, persist Layout+SVG+extrusion",
  "parameters": {
    "type": "object",
    "required": ["input_path"],
    "properties": {
      "input_path": {"type": "string"},
      "polish": {"type": "boolean", "default": false},
      "polish_tolerance": {"type": "number", "default": 1.0},
      "scale_meters_per_unit": {"type": ["number", "null"]},
      "scale_user_confirmed": {"type": "boolean", "default": false},
      "wall_height_m": {"type": "number", "default": 2.7}
    }
  },
  "returns": {
    "layout_id": "uuid",
    "geometry_fingerprint": "string",
    "source_kind": "image|pdf|text",
    "svg": "string",
    "extrusion": "object",
    "geometry": "object"
  }
}
```

### 4. Resource bounds & efficiency gains

| Bound | Value |
|-------|--------|
| Sequential stages | Normalize → Infer → Persist (no parallel geometry engines) |
| LLM tokens on this path | **Zero** for geometry (specialist model only) |
| Unit test path | `infer_fn` injection — no detectron2/GPU required |
| Live infer path | GPU/MPS/CUDA + detectron2/ops; may skip on Mac |
| Determinism | Identical polygon inputs → identical `geometry_fingerprint` |
| DB | One transaction: `layouts` insert + `audit_log` insert |

### 5. Degradation & fault isolation (NASA §6.4)

| Scenario | Exception / behavior |
|----------|----------------------|
| Missing input file | `ParseAndMapError` — no DB write |
| Normalize unsupported type | `UnsupportedInputError` / `InputNotFoundError` |
| Infer empty polygons | `ParseAndMapError("infer produced empty polygon sequence")` |
| Infer wrong type | `ParseAndMapError` on non-`PolygonSequenceResult` |
| Live R2S runtime missing | `Raster2SeqRuntimeError` when `infer_fn is None`; **no** fallback engine |
| Persist failure | `PersistError`; no silent success |
| Partial success | Forbidden: do not write layout without polygons |

---

## OCR-03a-INPUT-NORMALIZE

### 1. Component ID & system boundary

| Field | Specification |
|-------|----------------|
| **Component ID** | OCR-03a-INPUT-NORMALIZE |
| **Name** | Floorplan input normalization |
| **Status** | AS-BUILT |
| **Runtime locus** | Python: `services/floorplan_input` |
| **Boundary** | Pure function plane; no network; no LLM |

### 2. Stakeholder policy allocation

| Policy | Allocation |
|--------|------------|
| TS1 step: Input Normalization | Owner |
| Multi-modal image + PDF→raster (Poppler) | Owner |
| Phase 0 Poppler dependency | Consumer of `poppler-utils` |
| Goal: multi-modal inputs | Entry gate for TS1 |

### 3. Interface control contracts

```python
def normalize_floorplan_input(path: str | Path, *, page: int = 1) -> NormalizedRaster

@dataclass(frozen=True)
class NormalizedRaster:
    rgb: np.ndarray          # HxWx3 uint8
    source_kind: Literal["image", "pdf"]  # (+ text reserved at DB)
    content_sha256: str
    page: int
    width: int
    height: int
```

**Errors:** `InputNotFoundError`, `UnsupportedInputError`, `InputConvertError`.

### 4. Resource bounds & efficiency gains

| Bound | Value |
|-------|--------|
| PDF page default | 1 |
| Output dtype | uint8 RGB only |
| Hash | SHA-256 of file bytes for identical-input detection |
| Memory | Single raster in process; no batch API |

### 5. Degradation & fault isolation (NASA §6.4)

| Scenario | Response |
|----------|----------|
| Missing Poppler for PDF | Convert error — fail closed |
| Corrupt image | Convert error — fail closed |
| Wrong dtype/shape | `ValueError` in `__post_init__` |

---

## OCR-03b-R2S-INFER

### 1. Component ID & system boundary

| Field | Specification |
|-------|----------------|
| **Component ID** | OCR-03b-R2S-INFER |
| **Name** | Raster2Seq inference adapter |
| **Status** | AS-BUILT (unit/mock); live integration **environment-gated** |
| **Runtime locus** | Python: `services/raster2seq_adapter` + vendored `Raster2Seq/` + local checkpoint |
| **Boundary** | Sole **primary geometry producer**. Outside Portal; outside C++ (Python sidecar) |

### 2. Stakeholder policy allocation

| Policy | Allocation |
|--------|------------|
| TS1 Core Reconstruction Engine | Owner |
| Raster2Seq sole floorplan engine | Enforced |
| Checkpoint cubicasa5k / haopt/Raster2Seq | Default alias |
| Optional Douglas-Peucker polish post-only | Owner; **default off** |
| Phase 2 inference | Owner |

### 3. Interface control contracts

```python
def infer_polygons(
    source: NormalizedRaster | Path | str,
    *,
    polish: bool = False,
    polish_tolerance: float = 1.0,
    checkpoint_alias: str = "cubicasa5k",
    checkpoint_path: str | Path | None = None,
    _generate_fn=None,  # test injection
    _model=None,
) -> PolygonSequenceResult

@dataclass(frozen=True)
class PolygonItem:
    id: str
    label: str
    kind: str   # room | door | window | other
    points: list[list[float]]  # [[x,y], ...]

@dataclass(frozen=True)
class PolygonSequenceResult:
    polygons: list[PolygonItem]
    checkpoint_alias: str
    checkpoint_path: str
    checkpoint_repo: str
    image_size: int
    polish_applied: bool
    source_content_sha256: str | None
```

**Checkpoint path (on disk, not in git):**  
`Raster2Seq/checkpoints/cubicasa5k/checkpoint.pth`

**Errors:** `CheckpointNotFoundError`, `Raster2SeqRuntimeError`.

### 4. Resource bounds & efficiency gains

| Bound | Value |
|-------|--------|
| Geometry LLM calls | **None** |
| Polish | Post-only; default **false** |
| Live deps | torch + detectron2/ops as required by vendored model |
| Unit path | `_generate_fn` / outer `infer_fn` injection |
| Image size | From checkpoint `config.json` inference_args (typically 256) |

### 5. Degradation & fault isolation (NASA §6.4)

| Scenario | Response |
|----------|----------|
| Missing checkpoint | `CheckpointNotFoundError` |
| Missing detectron2/ops | `Raster2SeqRuntimeError`; integration tests **skip** with documented reason |
| Alternate geometry engine proposed | **Forbidden** — fail closed |
| Polish on | Must not change model weights; only post-process rings |

---

## OCR-03c-LAYOUT-BUILD-PERSIST

### 1. Component ID & system boundary

| Field | Specification |
|-------|----------------|
| **Component ID** | OCR-03c-LAYOUT-BUILD-PERSIST |
| **Name** | Layout JSON + 2D SVG + 3D extrusion + Postgres persist |
| **Status** | AS-BUILT |
| **Runtime locus** | Python: `services/layout_builder` |
| **Boundary** | Pure geometry transforms + DB writer; no inference |

### 2. Stakeholder policy allocation

| Policy | Allocation |
|--------|------------|
| TS1: write structured layout JSON to Postgres | Owner |
| 2D view from polygons | SVG emitter owner |
| 3D deterministic extrusion of verified 2D | Owner |
| Identical inputs → identical geometry | `geometry_fingerprint` owner |
| Phase 1 tables `layouts`, `audit_log` | Writer |
| ADR 0003 2D authoritative | Enforced: extrusion footprints = 2D points |

### 3. Interface control contracts

**Build**

```python
def build_layout(polygons: Sequence[PolygonItem] | PolygonSequenceResult, *, ...) -> LayoutBuildResult
def build_and_persist_layout(polygons, *, conn, ...) -> LayoutRow
```

**Layout `geometry` JSON (AS-BUILT shape)**

```json
{
  "schema_version": "1",
  "source": {"kind": "image|pdf", "content_sha256": "hex"},
  "checkpoint": {"alias": "cubicasa5k", "repo": "haopt/Raster2Seq", "image_size": 256},
  "scale": {"meters_per_unit": null, "user_confirmed": false},
  "polygons": [
    {"id": "p0", "label": "kitchen", "kind": "room", "points": [[0.0, 0.0], [10.0, 0.0]]}
  ]
}
```

**Extrusion JSON (AS-BUILT)**

```json
{
  "wall_height_m": 2.7,
  "door": {"sill_m": 0.0, "height_m": 2.1},
  "window": {"sill_m": 0.9, "height_m": 1.2},
  "nodes": [
    {
      "id": "p0",
      "kind": "room",
      "label": "kitchen",
      "footprint": [[0.0, 0.0], [10.0, 0.0]],
      "extrude": {"z0": 0.0, "z1": 2.7}
    }
  ]
}
```

**Postgres `layouts` columns (AS-BUILT migration)**  
`id, schema_version, source_kind, content_sha256, checkpoint_alias, checkpoint_repo, scale_meters_per_unit, scale_user_confirmed, geometry, svg, extrusion, created_at, updated_at`

**Audit action string:** `layout.build_and_persist`  
**Audit detail JSON:** `{content_sha256, checkpoint_alias, polygon_count, geometry_fingerprint}`

**Fingerprint:** SHA-256 of canonical JSON `{geometry, svg, extrusion}` (`canonicalize.geometry_fingerprint`).

### 4. Resource bounds & efficiency gains

| Bound | Value |
|-------|--------|
| Wall height default | 2.7 m |
| Coord quantize | 6 decimals geometry; 3 decimals SVG |
| CPU only | No GPU |
| Transaction | Single TX for layout + audit success path |

### 5. Degradation & fault isolation (NASA §6.4)

| Scenario | Response |
|----------|----------|
| Zero valid polygons | `LayoutBuilderError` |
| Invalid `source_kind` | `LayoutBuilderError` |
| DB down | `PersistError` |
| Extrusion inventing vertices | **Forbidden by construction** — footprint copy only |

---

## OCR-04-TS2-OPTIMIZE-KITCHEN

### 1. Component ID & system boundary

| Field | Specification |
|-------|----------------|
| **Component ID** | OCR-04-TS2-OPTIMIZE-KITCHEN |
| **Name** | Task Sequence 2 — `optimize_kitchen` |
| **Status** | REQUIRED-NOT-BUILT |
| **Runtime locus** | Tool invoked from OCR-01; deterministic optimizer core (Hexaly C++ / OR-Tools / cuOpt per goal); Grok for plan/aesthetic judgment only |
| **Boundary** | **Consumes** Layout polygons from OCR-05; **must not** regenerate walls |

### 2. Stakeholder policy allocation

| Policy | Allocation |
|--------|------------|
| **Task Sequence 2** finishes + inspiration → complete system | Owner |
| Sub-sequence 2-a/2-b/2-c | Owner |
| Catalog-compliant, storage-optimized, design-feel aligned | Owner |
| Models: Plan Grok; Review checker+Grok; Implement = optimizer code | Split: LLM judgment vs deterministic placement |
| Phase 4 intelligence wiring (partial) | Consumer of OCR-06/07 |
| Parallelizable retrieval/scoring | Allowed as **parallel tools inside OCR-01** |

### 3. Interface control contracts

**MCP tool (REQUIRED-NOT-BUILT)**

```json
{
  "name": "optimize_kitchen",
  "parameters": {
    "type": "object",
    "required": ["layout_id"],
    "properties": {
      "layout_id": {"type": "string", "format": "uuid"},
      "finish_ids": {"type": "array", "items": {"type": "string", "format": "uuid"}},
      "inspiration_uris": {"type": "array", "items": {"type": "string", "format": "uri"}},
      "objectives": {
        "type": "object",
        "properties": {
          "storage_weight": {"type": "number"},
          "aesthetic_weight": {"type": "number"}
        }
      }
    }
  },
  "returns": {
    "session_id": "uuid",
    "placements": [
      {
        "id": "cab_001",
        "sku": "string",
        "x": 0.0,
        "y": 0.0,
        "rotation_deg": 0.0,
        "model_url": "https://cdn.example/cab.glb"
      }
    ],
    "constraint_report": {"collisions": 0, "out_of_bounds": 0},
    "verified": true
  }
}
```

**Scene state (goal §3.1 DB example)**

```json
{
  "cabinets": [
    {"id": "cab_001", "x": 10, "y": 0, "model_url": "cdn.site.com/cab.glb", "sku_id": "SKU"}
  ]
}
```

**Collision checks:** shapely/GEOS against Raster2Seq polygons (goal §4 table).

### 4. Resource bounds & efficiency gains

| Bound | Rule |
|-------|------|
| Geometry source | Layout from OCR-05 only |
| LLM role | Planning/aesthetic — **not** coordinate invention for walls |
| One-shot render | Only after verification (2-c) |
| Parallel tools | Catalog retrieval + CLIP scoring inside single C++ loop |
| Token cost | Avoid multi-agent plan/review/test/coder graph on high-volume path |

### 5. Degradation & fault isolation (NASA §6.4)

| Scenario | Response |
|----------|----------|
| Missing layout_id | Reject tool call |
| Constraint fail | Return `verified: false` + report; **no** one-shot Cosmos beautify as fix |
| Optimizer unavailable | Fail tool; do not LLM-hallucinate placements |
| Inspiration embedder down | Degrade aesthetic term; keep hard constraints |

---

## OCR-05-DATA-PLANE

### 1. Component ID & system boundary

| Field | Specification |
|-------|----------------|
| **Component ID** | OCR-05-DATA-PLANE |
| **Name** | Postgres/Neon + pgvector data plane |
| **Status** | AS-BUILT schema (`db/migrations/001_phase1_data_plane.sql`); catalog seed PARTIAL/empty |
| **Runtime locus** | PostgreSQL 16+ with extensions `vector`, `pgcrypto` |
| **Boundary** | Shared persistence for all tools; single source of truth for Layout |

### 2. Stakeholder policy allocation

| Policy | Allocation |
|--------|------------|
| Phase 1 – Data Plane | Owner |
| Tables: cabinets, finishes, layouts, sessions, audit_log | Owner |
| Layout geometry JSON + scale | Storage for TS1 |
| Embeddings for catalog/aesthetic | Schema ready (`vector(512)` on cabinets) |
| Session resume without re-reconstruction | `sessions.layout_id` FK |

### 3. Interface control contracts

**Connection env:** `PLANNER_AI_DATABASE_URL` | `DATABASE_URL` | default `postgresql://localhost/planner_ai`

**Tables (AS-BUILT):** see migration — `layouts`, `cabinets`, `finishes`, `sessions`, `audit_log` with columns and FKs as in `001_phase1_data_plane.sql`.

**Access pattern:** Python `psycopg` via `layout_builder.connect()`; future C++ via libpq or tool-only access (prefer tools for ETE boundary clarity).

### 4. Resource bounds & efficiency gains

| Bound | Rule |
|-------|------|
| Layout authority | `layouts.geometry` + `svg` + `extrusion` |
| GIN index | `layouts_geometry_gin` on geometry jsonb |
| Embedding dim | 512 (cabinets) until catalog slice revises |
| CDN | GLB binaries **not** in DB — URLs only |

### 5. Degradation & fault isolation (NASA §6.4)

| Scenario | Response |
|----------|----------|
| DB unreachable | Tools fail closed; Portal shows error |
| FK violation | Transaction rollback |
| Concurrent layout writes | Separate UUIDs; fingerprint compares geometry not id |

---

## OCR-06-INTEL-GROK

### 1. Component ID & system boundary

| Field | Specification |
|-------|----------------|
| **Component ID** | OCR-06-INTEL-GROK |
| **Name** | Interactive / planning intelligence (Grok-4.5) |
| **Status** | REQUIRED-NOT-BUILT (routing policy defined) |
| **Runtime locus** | External xAI OpenAI-compatible HTTP API |
| **Boundary** | Intelligence layer; **not** geometry authority |

### 2. Stakeholder policy allocation

| Policy | Allocation |
|--------|------------|
| Routing: interactive chat, planning, refinement, storage reasoning | Owner |
| TS2 plan / aesthetic judgment | Co-owner with OCR-04 |
| Phase 4 – Intelligence Wiring | Partial owner |
| Must not replace Raster2Seq | Hard constraint |

### 3. Interface control contracts

```http
POST {XAI_OPENAI_BASE}/v1/chat/completions
Authorization: Bearer <XAI_API_KEY>
```

Payload: standard OpenAI chat schema. **No** floorplan polygon emission contract — if model emits coordinates, OCR-01 **must discard** for wall geometry.

### 4. Resource bounds & efficiency gains

| Bound | Rule |
|-------|------|
| Use on high-volume loops | Minimize; prefer tools + cache |
| Commoditized pricing | Flash/mid-tier effective cost target for background (goal core requirements) |
| Context | Prefer layout_id references over re-pasting full SVG |

### 5. Degradation & fault isolation (NASA §6.4)

| Scenario | Response |
|----------|----------|
| API down | Interactive degrade; TS1/TS2 tools still callable |
| Hallucinated walls | Policy filter — geometry only from OCR-03 |
| Cost spike | Rate limit; force tool-only mode |

---

## OCR-07-INTEL-COSMOS

### 1. Component ID & system boundary

| Field | Specification |
|-------|----------------|
| **Component ID** | OCR-07-INTEL-COSMOS |
| **Name** | Generation / spatial synthesis assist (Cosmos 3) |
| **Status** | REQUIRED-NOT-BUILT |
| **Runtime locus** | Cosmos 3 Nano / Super / 4-Step (HF collections / cosmos-framework) |
| **Boundary** | **Synthesis Path only after placement locked** — not Reconstruction Path |

### 2. Stakeholder policy allocation

| Policy | Allocation |
|--------|------------|
| Routing: one-shot kitchen synthesis / high-fidelity generation | Owner when used |
| Optional textures/views after deterministic placement | Owner |
| Phase 4 / Phase 6 route generation-heavy work to 4-Step | Owner |
| Never primary floorplan engine | Enforced |

### 3. Interface control contracts

**Input (REQUIRED-NOT-BUILT)**

```json
{
  "layout_id": "uuid",
  "placements": [],
  "mode": "texture_assist|alt_view",
  "model_variant": "cosmos-nano|cosmos-4step"
}
```

**Output:** media URIs / tensors — **not** authoritative wall polygons.

### 4. Resource bounds & efficiency gains

| Bound | Rule |
|-------|------|
| Prefer distilled 4-Step | Phase 6 |
| Call frequency | After verification only |
| Token/GPU | Isolate from C++ agent process when possible |

### 5. Degradation & fault isolation (NASA §6.4)

| Scenario | Response |
|----------|----------|
| Cosmos down | Skip synthesis; keep Layout + placements |
| Attempt to use as geometry source | **Hard reject** |

---

## OCR-08-VIEWER-2D3D

### 1. Component ID & system boundary

| Field | Specification |
|-------|----------------|
| **Component ID** | OCR-08-VIEWER-2D3D |
| **Name** | 2D Konva + 3D Three.js / openPlan3D viewer |
| **Status** | REQUIRED-NOT-BUILT (openPlan3D/three.js trees vendored) |
| **Runtime locus** | Browser (Portal OCR-02); optional openPlan3D SvelteKit |
| **Boundary** | Presentation only; consumes Layout + scene state |

### 2. Stakeholder policy allocation

| Policy | Allocation |
|--------|------------|
| TS1 2D View (Konva.js) layers grid/walls/furniture | Owner |
| TS1 3D View (Three.js) InstancedMesh + GLTF/Draco | Owner |
| openPlan3D complementary editor | Optional integration |
| Phase 2/5 viewer integration | Owner |
| 2D authoritative edits (future) | Must persist to OCR-05 |

### 3. Interface control contracts

**2D input:** `layouts.svg` or `geometry.polygons`  
**3D input:** `layouts.extrusion` + placement list with `model_url`  
**User edit event (future)**

```json
{
  "type": "placement_update",
  "layout_id": "uuid",
  "entity": {"sku_id": "string", "x": 0.0, "y": 0.0, "rotation": 0.0}
}
```

### 4. Resource bounds & efficiency gains

| Bound | Rule |
|-------|------|
| GLB | CDN edge fetch; Draco ~40% size reduction (goal) |
| Instancing | One GLB → many instances |
| Spin up/down | Milliseconds for view toggle |

### 5. Degradation & fault isolation (NASA §6.4)

| Scenario | Response |
|----------|----------|
| WebGL fail | 2D SVG only |
| Missing GLB | Placeholder mesh; keep footprint from extrusion |
| Desync with DB | Re-fetch by layout_id + fingerprint |

---

## OCR-09-MCP-TOOL-SURFACE

### 1. Component ID & system boundary

| Field | Specification |
|-------|----------------|
| **Component ID** | OCR-09-MCP-TOOL-SURFACE |
| **Name** | MCP / OpenAI tool bridge |
| **Status** | REQUIRED-NOT-BUILT (highest leverage next build per Slice A handoff) |
| **Runtime locus** | Process boundary between OCR-01 (C++) and Python tools OCR-03/04 |
| **Boundary** | **Only** sanctioned path for agent→reconstruction/optimize |

### 2. Stakeholder policy allocation

| Policy | Allocation |
|--------|------------|
| Phase 2: expose `parse_and_map_floorplan` as MCP/microservice | Owner |
| Phase 3: agent parallel tool dispatch | Owner |
| Phase 5: enable MCP tools in Portal | Config consumer |
| ETE: tools not multi-agent chat | Owner |
| Audit all tool calls | Emits to OCR-11 |

### 3. Interface control contracts

**Transport options (either is compliant)**

1. MCP tool registration (JSON-RPC style tool list/call)  
2. HTTP microservice:

```http
POST /tools/parse_and_map_floorplan
Content-Type: application/json

{"input_path": "/data/plan.png", "polish": false, "scale_meters_per_unit": 0.01}
```

**Response**

```json
{
  "ok": true,
  "layout_id": "uuid",
  "geometry_fingerprint": "hex",
  "source_kind": "image",
  "svg": "<svg>...</svg>",
  "extrusion": {},
  "geometry": {},
  "duration_ms": 0
}
```

**Error envelope**

```json
{
  "ok": false,
  "error_type": "ParseAndMapError|Raster2SeqRuntimeError|PersistError|...",
  "message": "string",
  "retryable": false
}
```

### 4. Resource bounds & efficiency gains

| Bound | Rule |
|-------|------|
| Auth | Local/loopback or mTLS in prod — not public anonymous |
| Timeout | Per-tool deadline (reconstruction longer than catalog query) |
| Payload size | Cap SVG inline size; allow layout_id-only responses for chat |
| Parallelism | Safe concurrent tools if DB-safe; TS1 remains internally sequential |

### 5. Degradation & fault isolation (NASA §6.4)

| Scenario | Response |
|----------|----------|
| Python worker down | `ok:false`, retryable true |
| Schema mismatch | Reject; do not coerce geometry |
| Portal calls tool storm | Rate limit; autonomous path uses OCR-10 quotas |

---

## OCR-10-AUTONOMOUS-BG-LOOP

### 1. Component ID & system boundary

| Field | Specification |
|-------|----------------|
| **Component ID** | OCR-10-AUTONOMOUS-BG-LOOP |
| **Name** | High-volume autonomous design iteration loop |
| **Status** | REQUIRED-NOT-BUILT |
| **Runtime locus** | **Inside OCR-01 C++ process** (or sibling worker sharing tool plane) — **never Portal** |
| **Boundary** | Background jobs: refine placements, re-score, batch sessions |

### 2. Stakeholder policy allocation

| Policy | Allocation |
|--------|------------|
| High-volume autonomous loops never touch portal | **Defining constraint** |
| ETE metrics / load test Phase 8 | Owner of measurement harness |
| Phase 6 portal bypass | Owner |
| Controlled parallel tools | Owner |

### 3. Interface control contracts

**Job envelope**

```json
{
  "job_id": "uuid",
  "type": "iterate_kitchen|batch_parse",
  "session_id": "uuid",
  "layout_id": "uuid",
  "max_iterations": 10,
  "tools_allowed": ["optimize_kitchen"],
  "forbid_portal": true
}
```

**Completion**

```json
{
  "job_id": "uuid",
  "status": "succeeded|failed|cancelled",
  "iterations": 0,
  "token_metrics": {"prompt_tokens": 0, "completion_tokens": 0, "tool_calls": 0},
  "final_layout_id": "uuid",
  "audit_refs": []
}
```

### 4. Resource bounds & efficiency gains

| Bound | Rule |
|-------|------|
| Portal HTTP | **Forbidden** (`forbid_portal: true` enforced) |
| Token target | Meet ~50% steps / ~4× output reduction vs multi-agent baseline |
| Cache | Warm KV with layout+catalog prefix |
| Concurrency | Job queue with GPU/CPU pools; not multi-agent debate |

### 5. Degradation & fault isolation (NASA §6.4)

| Scenario | Response |
|----------|----------|
| Iteration budget exhausted | Stop; persist last verified state |
| Tool fail mid-job | Mark failed; no partial unverified kitchen as success |
| Accidental Portal dependency | Static analysis / runtime assert fail job |

---

## OCR-11-AUDIT-OBS

### 1. Component ID & system boundary

| Field | Specification |
|-------|----------------|
| **Component ID** | OCR-11-AUDIT-OBS |
| **Name** | Audit log + observability |
| **Status** | PARTIAL — `audit_log` AS-BUILT; OpenTelemetry/Prometheus Phase 7 REQUIRED-NOT-BUILT |
| **Runtime locus** | Postgres `audit_log`; future OTel exporters |
| **Boundary** | Cross-cutting technical management (NASA §6) |

### 2. Stakeholder policy allocation

| Policy | Allocation |
|--------|------------|
| All tool calls and routing decisions audited | Owner |
| Phase 7 observability | Owner |
| Cost/token metrics Phase 8 | Data source |

### 3. Interface control contracts

**AS-BUILT insert (layout path)**

```sql
INSERT INTO audit_log (actor, action, layout_id, success, duration_ms, detail)
VALUES ('system', 'layout.build_and_persist', $layout_id, true, $ms, $detail_jsonb);
```

**REQUIRED future actions (examples)**  
`agent.tool_call`, `agent.route`, `optimize_kitchen.run`, `autonomous.job_*`

**detail JSON minimum**

```json
{
  "tool": "string",
  "route": "raster2seq|grok|cosmos|forbidden",
  "geometry_fingerprint": "string|null",
  "token_usage": {"prompt": 0, "completion": 0},
  "error": "string|null"
}
```

### 4. Resource bounds & efficiency gains

| Bound | Rule |
|-------|------|
| Write path | Async-capable later; today sync in TX with layout |
| Retention | Ops-defined; index on `occurred_at DESC`, `action` |
| PII | No raw floorplan blobs in audit — hashes/ids only |

### 5. Degradation & fault isolation (NASA §6.4)

| Scenario | Response |
|----------|----------|
| Audit insert fails after layout | Prefer TX atomicity (current design); if split, alert critical |
| OTel collector down | Local logs still required; do not block TS1 |

---

## Allocation matrix (Component × Task Sequence × Phase)

| Component | TS1 parse_and_map | TS2 optimize_kitchen | Interactive chat | Autonomous BG | Phase |
|-----------|-------------------|----------------------|------------------|---------------|-------|
| OCR-01 | Routes | Routes | Primary | Hosts OCR-10 | 3,6 |
| OCR-02 | UX trigger only | UX trigger only | Primary UX | **Forbidden** | 5 |
| OCR-03* | **Execute** | — | via tools | via tools | 2 |
| OCR-04 | — | **Execute** | via tools | via tools | 2–4 |
| OCR-05 | Persist/read | Persist/read | Session | Session | 1 |
| OCR-06 | — | Plan/aesthetic | Primary model | Minimize | 4 |
| OCR-07 | — | Optional after verify | Optional | Rare | 4,6 |
| OCR-08 | Display | Display | Display | — | 2,5 |
| OCR-09 | Bridge | Bridge | Bridge | Bridge | 2,3 |
| OCR-10 | Batch optional | Iterate | — | **Primary** | 6,8 |
| OCR-11 | Audit | Audit | Audit | Audit | 1,7 |

---

## Interface N² (who may call whom)

| From \ To | 01 | 02 | 03 | 04 | 05 | 06 | 07 | 08 | 09 | 10 | 11 |
|-----------|----|----|----|----|----|----|----|----|----|----|-----|
| 01 C++ loop | — | no* | via 09 | via 09 | via tools | yes | yes | no | yes | hosts | yes |
| 02 Portal | yes | — | no direct** | no direct** | read | no | no | embeds | MCP cfg | no | read |
| 03 TS1 | no | no | — | no | write | no | no | no | no | no | write |
| 04 TS2 | no | no | no | — | read/write | yes | optional | no | no | no | write |
| 09 MCP | serves 01 | serves 02 | invokes | invokes | — | — | — | — | — | serves 10 | write |

\*Portal may call 01; 01 must not call Portal for OCR-10.  
\**Portal reaches 03/04 only through 01+09, not by embedding Python in the browser.

---

## Forbidden allocations (explicit)

| Forbidden | Rationale (goal.md) |
|-----------|---------------------|
| Multi-agent planner/reviewer/tester/coder graph on high-volume TS1/TS2 | Sequential reconstruction; 10–15× token cost; ETE violation |
| Grok or Cosmos as wall geometry source | Raster2Seq sole engine |
| Autonomous loops via Open WebUI | Portal bypass mandatory |
| Second classical CV floorplan engine as primary | Architecture law |
| 3D mesh inventing walls independent of 2D Layout | ADR/goal 2D authority |
| Committing Raster2Seq weights to git | Ops/size policy |

---

## Verification hooks (as-built)

```bash
cd /Users/shayanbozorgmanesh/Developer/planner-ai
.venv/bin/pytest tests/ -m "not integration" -q
# Expect: 39 passed (Slice A unit path) as of closeout 85745c4 era
```

Authoritative session gates: `docs/session/2026-08-01-slice-a-gates.md`  
Next-agent handoff: `docs/session/2026-08-01T222306-0400-handoff-slice-a-next.md`

---

*End of Operational Component Registry. Authority: `docs/goal.md`. SE risk framing: NASA/SP-2016-6105 Rev2 §6.4.*
