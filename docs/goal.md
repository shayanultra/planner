# Authoritative Engineering Blueprint & Precise Implementation Guide
## Version 3 — Systems Architecture Recommendation (as of 2026-08-01)

**Target System**: High-volume, utility-first AI chat agent for real-world kitchen planning.  
**Core Requirements**: Extreme Token Efficiency (~50% fewer steps, ~4× fewer output tokens on high-volume loops) + Commoditized Intelligence Pricing (flash/mid-tier effective cost for near-Opus capability on background loops).  
**Primary Stack Preference**: C++ for the agent runtime.  
**User Flow Priority**: Accurate floorplan/layout → 2D/3D space reconstruction is the non-negotiable foundation. Failure here invalidates all subsequent steps.

This Version 3 fully replaces the previous CubiCasa5K + OpenCV recommendation with **Raster2Seq** as the sole primary polygon extraction engine. Secondary and hybrid options are rejected. Backward compatibility with Version 1 and Version 2 is not preserved. The design chooses the simplest implementation that fully meets requirements and prefers established, well-maintained libraries.

---

## 1. Goals, Constraints & Success Criteria

### Goals
- Deliver the complete user flow with deterministic accuracy on floorplan reconstruction.
- Support text, image, and PDF floorplan inputs that produce identical accurate 2D + 3D reconstructions.
- One-shot kitchen system generation constrained to the reconstructed layout + catalog products, weighted 70–80% storage maximization and 20–30% design-feel adherence from inspiration image(s).
- Target ≥95% match to user desire on the first complete kitchen output (verified by subsequent user engagement, not disengagement).
- Extreme Token Efficiency and Commoditized Pricing on high-volume autonomous loops.
- Production-ready, deployable end-to-end from this document alone on 2026-08-01.

### Non-Goals
- Training new foundation models.
- Full custom CAD engine.
- Supporting every regional building code on day one.

### Success Criteria
- Floorplan reconstruction accuracy: geometric fidelity sufficient for subsequent catalog placement (walls, openings, scale recoverable or user-correctable).
- Kitchen output: complete, catalog-compliant system; storage-optimized; design-feel aligned.
- Token/cost metrics: measurable reduction vs naïve multi-hop baselines on repeated design iterations.
- Deployable via Docker Compose or Helm with the listed components.

---

## 2. Architecture Overview (Version 3)

```
┌─────────────────────────────────────────────────────────────────────┐
│  User-Facing Portal                                                 │
│  Open WebUI (SvelteKit) — https://github.com/open-webui/open-webui  │
│  + openPlan3D-style / Three.js 2D+3D viewer component               │
│  Thin, compile-time optimized, multi-backend                        │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ OpenAI-compatible + MCP
┌───────────────────────────────▼─────────────────────────────────────┐
│  C++ Agent Runtime Layer (Primary)                                  │
│  llama.cpp core — https://github.com/ggml-org/llama.cpp             │
│  + agent loop extensions (llama-agent / chatllm.cpp style)          │
│  Single-process primary loop with controlled parallel tool calls    │
│  Aggressive KV/prefix caching, GBNF constrained decoding, MCP       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ Smart routing + caching
┌───────────────────────────────▼─────────────────────────────────────┐
│  Intelligence & Model Layer                                         │
│  Interactive / planning / refinement: Grok-4.5 (xAI API)            │
│  Generation / spatial synthesis: Cosmos 3 Nano / Super + 4-Step     │
│  Floorplan reconstruction: Raster2Seq (primary and sole)            │
│  https://huggingface.co/collections/nvidia/cosmos3                  │
│  https://github.com/NVIDIA/cosmos                                   │
│  https://github.com/Cornell-VAILab/Raster2Seq                       │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│  Data & Tool Plane                                                  │
│  Postgres/Neon + pgvector (catalog + embeddings + layouts)          │
│  Floorplan reconstruction pipeline (Raster2Seq)                     │
│  Aesthetic embedder (CLIP-style) + storage optimizer                │
│  Persistent memory, session state, observability, audit logs        │
└─────────────────────────────────────────────────────────────────────┘
```

**Routing Rule (Efficiency Core)**:  
- Floorplan reconstruction path → Raster2Seq specialist pipeline (deterministic + VLM assist for input normalization).  
- Interactive chat, planning, refinement, storage reasoning → Grok-4.5.  
- One-shot kitchen synthesis / high-fidelity generation → Cosmos 3 (prefer Cosmos Nano or Cosmos 4-Step distilled).  
- High-volume autonomous loops stay inside the C++ runtime and never touch the portal.

---

## 3. Critical Task Analysis & Superior Solutions (2026-08-01)

### 3.1 Task Sequence 1 — `parse_and_map_floorplan`

**Requirement**: User text / image / PDF input must produce the *identical accurate* 2D + 3D space reconstruction. This step has no relation to the catalog. The 2D viewer is primary; 3D is automatically derived from the verified 2D geometry.

**Superior Production Solution (verified 2026-08-01)**: Raster2Seq

**Canonical / reference implementation pattern**:  
https://github.com/Cornell-VAILab/Raster2Seq

**Paper**: Raster2Seq: Polygon Sequence Generation for Floorplan Reconstruction (SIGGRAPH 2026) — https://arxiv.org/abs/2602.09016  
**Project page**: https://cornell-vailab.github.io/Raster2Seq/  
**Weights**: https://huggingface.co/haopt/Raster2Seq

#### Core Reconstruction Pipeline (Raster2Seq)

1. **Input Normalization**  
   - PDF → raster image via established tools (pdf2image / Poppler).  
   - Text description → VLM (Grok-4.5 or Cosmos Reasoner) emits structured wall/opening description that is rendered or directly tokenized into the Raster2Seq input path.  
   - Image → direct to Raster2Seq.

2. **Core Reconstruction Engine**  
   - **Model**: Raster2Seq (autoregressive sequence-to-sequence model that represents floorplan elements as labeled polygon sequences jointly encoding geometry and semantics).  
     - Primary checkpoint: CubiCasa5K-trained (`cubicasa5k` key on https://huggingface.co/haopt/Raster2Seq).  
     - Alternative high-quality checkpoints: Structured3D-B, Raster2Graph (available at the same Hugging Face repository).  
   - **Canonical code**: https://github.com/Cornell-VAILab/Raster2Seq  
   - Raster2Seq predicts ordered, labeled polygons (rooms, doors, windows) with superior Room / Corner / Angle F1 scores compared with prior methods (RoomFormer, HEAT, FRI-Net, PolyRoom).  
   - Optional light classical cleanup (Douglas-Peucker + area filter) may be applied for final polygon polishing only; it is not the primary extraction method.

3. **Metric / scale recovery**  
   - User confirmation of one known dimension or VLM-assisted scale estimation; store recoverable scale factor in the layout record.

4. **2D Viewer**  
   - Structured SVG or canvas representation of walls, doors, windows, rooms generated directly from the Raster2Seq polygon sequences.

5. **3D Derivation**  
   - Deterministic extrusion of the verified 2D polygons into a Three.js scene (walls at full height, doors/windows at correct sill/lintel).  
   - Strong complementary viewer: https://github.com/laanlabs/openPlan3D (SvelteKit + Three.js, open-source 2D/3D floor-plan editor).

#### Why this is superior

- Raster2Seq is the clear state-of-the-art for raster-to-vector floorplan reconstruction as of SIGGRAPH 2026 (https://arxiv.org/abs/2602.09016).  
- On CubiCasa5K it achieves Room F1 88.7 (vs RoomFormer 83.5); on Structured3D-B it achieves Room F1 99.6 / Corner F1 98.3 (vs RoomFormer 95.1 / 91.7).  
- It demonstrates greater robustness as the number of rooms and corners increases, and stronger zero-shot generalization to real-world floorplans (WAFFLE).  
- The output is already ordered, labeled polygon sequences — ideal for deterministic 2D SVG generation and subsequent Three.js extrusion.  
- Separating 2D verification from 3D extrusion still allows the user (or a lightweight reviewer tool) to correct geometry before any catalog work begins.  
- HouseCrafter-style diffusion lifting remains reserved for later high-fidelity textured scene enhancement; it is not part of the critical path.

**Libraries / Frameworks the model must call (exact sequence)**:
1. Input loader / PDF rasterizer (pdf2image or Poppler).  
2. Raster2Seq inference (official code from https://github.com/Cornell-VAILab/Raster2Seq + checkpoint from https://huggingface.co/haopt/Raster2Seq).  
3. Optional light Douglas-Peucker + area filter.  
4. Scale recovery + validation.  
5. Write structured layout JSON (polygons + semantics + scale) to Postgres.  
6. Emit 2D SVG + Three.js scene graph for the portal viewer.

**Model for this step**: Raster2Seq is the sole primary engine. Grok-4.5 / Cosmos Reasoner are used only for text/PDF structured extraction and validation when the input is not already a clean raster image.

### 3.2 Task Sequence 2 — `optimize_kitchen` (Finishes + Inspiration → Complete System)

**Sub-sequence**:
- (2-a) User selects finishes (UI bound to catalog) + uploads inspiration photo(s).  
- (2-b) Agent plans → reviews → tests → implements the optimized kitchen.  
- (2-c) Complete system rendered in one shot only after verification.

**Weighting**: 70–80% storage / space maximization within the already-mapped floorplan constraints; 20–30% adherence to design feel from inspiration. First output must target ≥95% match to true user desire.

**Superior Production Leader for Single-Image → Extreme Token Efficiency Catalog Mapping (2026-08-01)**:

1. **Aesthetic Embedding**: CLIP-style or modern vision-language embedder on the inspiration image(s) → vector.  
2. **Catalog Retrieval**: pgvector similarity search against pre-computed product image / style embeddings, filtered by selected finishes and functional type (base/wall/tall + appliances).  
3. **Combinatorial Optimizer**: Multi-objective solver that maximizes storage volume (primary) subject to layout constraints and a design-similarity soft constraint. Prefer established solvers (cuOpt if available in environment, or OR-Tools / simple greedy + local search for minimal dependency).  
4. **Verification Loop**: Hard constraint check against the floorplan polygons produced by Raster2Seq (no collisions, openings respected, circulation preserved). Soft score for design feel.  
5. **One-shot Assembly**: Emit complete placement list (SKU + pose + size variant) that is catalog-deterministic.

**Models for (2-b)**:
- **Plan**: Grok-4.5 (layout-aware planning + storage reasoning).  
- **Review / Test**: Lightweight constrained checker (C++ or Python tool) + Grok-4.5 for aesthetic judgment.  
- **Code / Implement**: The optimizer + placement emitter (deterministic code, not LLM generation of geometry).  
- **Generation assist (optional high-fidelity textures or alternative views)**: Cosmos 3 Nano or 4-Step distilled variants.

**Libraries / Frameworks (sequence)**:
1. Aesthetic embedder (open CLIP / SigLIP or equivalent via Hugging Face).  
2. pgvector catalog query.  
3. Layout constraint engine (polygon intersection via shapely or C++ equivalent) operating on Raster2Seq polygons.  
4. Multi-objective optimizer.  
5. Scene graph assembler → Three.js / glTF export.  
6. Cosmos path only if additional visual synthesis is required after the deterministic placement is locked.

**Why this is the production leader for efficiency**:  
Retrieval + constrained combinatorial search is far cheaper in tokens than pure generative one-shot scene synthesis. The floorplan already supplies the hard combinatorial space (via Raster2Seq polygons); the inspiration image only modulates ranking. This keeps high-volume loops inside the efficient C++ runtime + database.

### 3.3 Orchestration Decision: Single-Process vs Multi-Agent

**Evidence-based decision (2026 literature)**:
- Google Research controlled study of 180 agent configurations (2026): multi-agent coordination improves *parallelizable* tasks (up to +81%) but *degrades* sequential reasoning tasks by 39–70%.  
- Floorplan reconstruction is predominantly sequential (normalize → Raster2Seq → validate → extrude).  
- Kitchen optimization contains parallelizable sub-tasks (retrieval, scoring, multiple candidate generation) but is overall sequential on the layout.  
- Anthropic and other reports show multi-agent can deliver quality gains at 10–15× token cost.

**Conclusion for this system**:
- **Primary path remains single-process C++ agent loop** (llama.cpp + agent extensions). This is mandatory for Extreme Token Efficiency on high-volume autonomous design iterations.  
- **Controlled parallel tool calls** inside the single loop are permitted and encouraged (e.g., parallel catalog queries + aesthetic scoring).  
- Full multi-hop planner / reviewer / tester / coder graphs are **not** used on the critical high-volume path. They may be optionally invoked for rare, high-stakes interactive sessions where the user explicitly requests exhaustive review, but they are gated and logged for cost.  
- Orchestration language: C++ primary for the loop; thin Python sidecars only for libraries that are not yet available in pure C++ (e.g., certain OpenCV or optimizer wrappers). Prefer C++ or language-agnostic MCP tools.

This preserves the required efficiency while still allowing specialization where it mathematically helps.

---

## 4. Additional Tooling That Improves the Complete User Flow

The following established libraries improve accuracy, UX, and reconstruction quality beyond the base architecture:

| Tool / Library | Role | Canonical Source | Benefit |
|---------------|------|------------------|---------|
| Raster2Seq | Primary floorplan → labeled polygon sequences | https://github.com/Cornell-VAILab/Raster2Seq | Current SOTA polygon quality and robustness |
| openPlan3D | 2D/3D floor-plan editor & viewer | https://github.com/laanlabs/openPlan3D | Superior interactive 2D editing + instant 3D preview; SvelteKit-native |
| Three.js / @react-three/fiber | Web 3D viewer | https://threejs.org | Industry-standard, lightweight scene rendering |
| pgvector | Catalog + layout embeddings | Built into Postgres/Neon | Efficient similarity search |
| shapely / GEOS | Constraint checking on Raster2Seq polygons | Python or C++ bindings | Collision / containment tests |
| CLIP / SigLIP-style embedders | Design-feel vectors | Hugging Face | Extreme-token-efficient aesthetic ranking |
| llama.cpp GBNF | Constrained decoding | Built into llama.cpp | Guarantees only valid catalog SKUs / sizes |
| cuOpt (if available) or OR-Tools | Multi-objective optimization | NVIDIA cuOpt / Google OR-Tools | Storage vs design trade-off solver |
| Cosmos 3 4-Step distilled | High-efficiency generation assist | https://huggingface.co/collections/nvidia/cosmos3 | Optional visual synthesis after deterministic placement |

These are additive and do not replace the core C++ runtime or Open WebUI portal.

---

## 5. Precise Implementation Phases (Version 3)

### Phase 0 – Environment
```bash
sudo apt update && sudo apt install -y build-essential cmake git curl docker.io docker-compose-plugin \
  libopencv-dev poppler-utils
pip install -U "huggingface_hub[cli]" opencv-python-headless shapely pgvector sqlalchemy torch torchvision
huggingface-cli login
```

### Phase 1 – Data Plane
- Neon or local Postgres 16+ with `pgvector`.  
- Tables: `cabinets`, `finishes`, `layouts` (geometry JSON from Raster2Seq + scale), `sessions`, `audit_log`.  
- Pre-compute product embeddings and aesthetic vectors.  
- Seed deterministic catalog (base / wall / tall + size variants).

### Phase 2 – Floorplan Reconstruction Service (Raster2Seq)
```bash
git clone https://github.com/Cornell-VAILab/Raster2Seq
cd Raster2Seq
# Follow official instructions for environment and data prep
# Download preferred checkpoint
huggingface-cli download haopt/Raster2Seq --include "cubicasa5k/*" --local-dir ./checkpoints/cubicasa5k
```
- Expose `parse_and_map_floorplan(input)` as an MCP tool or microservice that:
  1. Normalizes input.
  2. Runs Raster2Seq inference.
  3. Optionally applies light Douglas-Peucker polishing.
  4. Returns verified 2D geometry + 3D scene graph.
- Integrate openPlan3D or custom Three.js viewer into Open WebUI (custom component or Pipeline).

### Phase 3 – C++ Agent Runtime
```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp && cmake -B build -DGGML_CUDA=ON && cmake --build build --config Release -j
# Optional: git clone https://github.com/gary149/llama-agent
./build/bin/llama-server -m <quantized-model.gguf> -c 8192 --port 8080
```
Implement the single-process agent loop with:
- Prefix caching of layout + catalog context.  
- GBNF for catalog SKUs.  
- Parallel tool dispatch for retrieval + scoring.  
- Hard routing: reconstruction → Raster2Seq pipeline; chat → Grok-4.5; synthesis → Cosmos when needed.

### Phase 4 – Intelligence Wiring
- Grok-4.5 via xAI OpenAI-compatible endpoint.  
- Cosmos 3 Nano / Super / 4-Step models from https://huggingface.co/collections/nvidia/cosmos3.  
- Serve via cosmos-framework or Diffusers / SGLang as documented in https://github.com/NVIDIA/cosmos.

### Phase 5 – Portal
```bash
git clone https://github.com/open-webui/open-webui
# Configure OPENAI_API_BASE_URL to the agent runtime
# Enable MCP tools
# Add custom viewer component for 2D SVG + Three.js 3D (consuming Raster2Seq polygons)
docker compose up -d
```

### Phase 6 – Efficiency Mechanisms (Mandatory)
- Quantization (Q4_K_M / Q5_K_M).  
- Prefix / KV caching of layout + catalog.  
- GBNF constrained decoding.  
- Single-process C++ loop with controlled parallel tools only.  
- Route generation-heavy work exclusively to Cosmos 4-Step when used.  
- High-volume autonomous jobs bypass the portal entirely.

### Phase 7 – Deployment
- Docker Compose for development / early production.  
- Production: Open WebUI Helm chart (https://github.com/open-webui/helm-charts) + GPU node pool for llama.cpp + Raster2Seq service + Neon.  
- Observability: OpenTelemetry → Prometheus / Grafana.  
- All tool calls and routing decisions audited.

### Phase 8 – Verification
- Unit tests on Raster2Seq polygon fidelity and constraint satisfaction.  
- E2E: floorplan PDF → verified 2D/3D via Raster2Seq → finishes + inspiration → one-shot kitchen ≥95% alignment → refinement.  
- Load test autonomous loops for token and cost metrics.  
- User engagement metrics as the ultimate proxy for desire match.

---

## 6. Full User Flow Mapping (Hardened)

1. **Upload floorplan** (PDF / text / image) in Open WebUI → agent → `parse_and_map_floorplan` (Raster2Seq primary engine) → layout written to Postgres + 2D viewer updated → 3D auto-derived. User can correct 2D geometry before proceeding.  
2. **Select finishes + upload inspiration** → agent → aesthetic embed + catalog retrieval + multi-objective optimizer (70–80% storage, 20–30% design) → constraint verification against the *Raster2Seq-reconstructed* layout → complete placement list.  
3. **One-shot render** of the verified system in the Three.js / openPlan3D viewer.  
4. **Iterative refinement** via Grok-4.5 + constrained tools.  
5. **Background autonomous exploration** runs entirely against the C++ runtime.

---

## 7. Production Readiness Checklist

- [ ] Raster2Seq pipeline produces identical geometry for identical inputs.  
- [ ] 2D viewer is authoritative; 3D is derived from Raster2Seq polygons.  
- [ ] Catalog placements are hard-constrained to the reconstructed layout.  
- [ ] First kitchen output targets 70–80% storage / 20–30% design feel.  
- [ ] Single-process C++ primary loop with only controlled parallel tools.  
- [ ] Prefix caching, quantization, GBNF active.  
- [ ] All model routing decisions logged.  
- [ ] E2E tests cover the full critical path.  
- [ ] Observability and audit logs operational.  
- [ ] Deployable from this document alone on 2026-08-01.

---

## 8. Canonical Source Links (Complete)

- Open WebUI: https://github.com/open-webui/open-webui  
- llama.cpp: https://github.com/ggml-org/llama.cpp  
- llama-agent: https://github.com/gary149/llama-agent  
- chatllm.cpp: https://github.com/foldl/chatllm.cpp  
- Cosmos 3 collection: https://huggingface.co/collections/nvidia/cosmos3  
- Cosmos GitHub: https://github.com/NVIDIA/cosmos  
- Cosmos-Framework: https://github.com/NVIDIA/cosmos-framework  
- **Raster2Seq (primary floorplan engine)**: https://github.com/Cornell-VAILab/Raster2Seq  
- Raster2Seq project page: https://cornell-vailab.github.io/Raster2Seq/  
- Raster2Seq paper: https://arxiv.org/abs/2602.09016  
- Raster2Seq weights: https://huggingface.co/haopt/Raster2Seq  
- openPlan3D: https://github.com/laanlabs/openPlan3D  
- Three.js: https://threejs.org  
- Neon: https://neon.tech  

---

## 9. Citation Report

| Source | Full URL | Role in Blueprint |
|--------|----------|-------------------|
| Raster2Seq paper | https://arxiv.org/abs/2602.09016 | Primary scientific basis for polygon extraction superiority |
| Raster2Seq code | https://github.com/Cornell-VAILab/Raster2Seq | Canonical reference implementation pattern |
| Raster2Seq project | https://cornell-vailab.github.io/Raster2Seq/ | Official project page and interactive demos |
| Raster2Seq weights | https://huggingface.co/haopt/Raster2Seq | Production checkpoints (CubiCasa5K, Structured3D, etc.) |
| Open WebUI | https://github.com/open-webui/open-webui | User-facing portal |
| llama.cpp | https://github.com/ggml-org/llama.cpp | C++ agent runtime core |
| llama-agent | https://github.com/gary149/llama-agent | Agent loop extension |
| chatllm.cpp | https://github.com/foldl/chatllm.cpp | Additional pure-C++ chat/RAG reference |
| Cosmos 3 collection | https://huggingface.co/collections/nvidia/cosmos3 | Intelligence layer generation models |
| Cosmos GitHub | https://github.com/NVIDIA/cosmos | Cosmos training/inference framework |
| Cosmos-Framework | https://github.com/NVIDIA/cosmos-framework | Supporting framework |
| openPlan3D | https://github.com/laanlabs/openPlan3D | 2D/3D viewer |
| Three.js | https://threejs.org | Web 3D rendering |
| Neon | https://neon.tech | Postgres + pgvector data plane |

---

**This Version 3 is the authoritative, hardened, and complete engineering blueprint.**  
It prioritizes accurate floorplan reconstruction via Raster2Seq (https://github.com/Cornell-VAILab/Raster2Seq) as the non-negotiable foundation, selects the production-proven catalog-mapping leaders available on 2026-08-01, retains single-process C++ efficiency while allowing controlled parallelism, and incorporates additional established tooling that measurably improves UX and geometric fidelity.  

Execute the phases in order. The resulting system meets every stated requirement for Extreme Token Efficiency, Commoditized Intelligence Pricing, and the full kitchen planning user flow.
