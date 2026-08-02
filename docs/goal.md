# "PLANNER AI" GOAL SPECIFICATION AND EXECUTION CONTRACT - AUGUST 1 2026. EXECUTE IMMEDIATELY.

**Objective:** Build the complete system described in the Authoritative Engineering Blueprint & Precise Implementation Guide.

## 1. Goals, Constraints & Success Criteria

### Goals
- Deliver the complete user flow with deterministic accuracy on floorplan reconstruction.
- Support multi-modal inputs that produce identical accurate 2D + 3D reconstructions.
- Room layout and kitchen system generation.
- Extreme Token Efficiency and Commoditized Pricing on high-volume autonomous loops.

### Non-Goals
- Training new foundation models.
- Full custom CAD engine.
- Supporting every regional building code on day one.

### Success Criteria
- Floorplan reconstruction and geometric fidelity with 98% accuracy or greater.
- Full kitchen design generation: catalog-compliant system; storage-optimized; design-feel aligned.
- Token/cost metrics: measurable reduction vs naïve multi-hop baselines on repeated design iterations.

# Authoritative Engineering Blueprint & Precise Implementation Guide
## Systems Architecture Recommendation (as of 2026-08-01)

**Target System**: Performance, utility-first AI chat agent for real-world kitchen planning.
**Core Requirements**: Extreme Token Efficiency (~50% fewer steps, ~4× fewer output tokens on high-volume loops) + Commoditized Intelligence Pricing (flash/mid-tier effective cost for near-Opus capability on background loops).  
**Primary Stack Preference**: C++ for the agent runtime.  
**User Flow Priority**: Accurate floorplan/layout → 2D/3D space reconstruction with 98% accuracy is the non-negotiable foundation.

## Workspace
`/Users/shayanbozorgmanesh/Developer/planner-ai`

## Authoritative sources (read from disk — do NOT restate in full)
1. `docs/goal.md` (sole architecture authority)
2. `AGENTS.md` + `docs/agents/*` — issue tracker (local `.scratch/`), triage labels, domain docs
3. `docs/session/*` - session handoffs.
4. `docs/openwiki/*` - agent documentation for the codebase. 

## CRITICAL RULES (non-negotiable):
- Do not preserve backward compatibility.
- Choose the simplest implementation that fully meets the current requirements.
- Prefer established, well-maintained libraries over custom implementation.
- Llama.cpp C++ primary agent runtime.
- Open WebUI SvelteKit Frontend.
- Raster2Seq floorplan reconstruction engine (https://github.com/Cornell-VAILab/Raster2Seq.git).
- Single-process C++ agent loop for Extreme Token Efficiency.
- Autonomous loops must never touch the user-facing chat interface portal.

## 2. Architecture Overview
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

## 3. Critical Task Analysis & Superior Solutions (2026-08-01)

# 3.1 Task Sequence 1 — `parse_and_map_floorplan`

## Objectives
**Objective #1**: Generate a 2D floorplan the from User's multi-modal input.
**Objective #2**: Achieve 98% accuracy output across 10,000 generated 2D floorplans.
**Objective #3**: Achieve average time-to-output of 2.0 seconds across 10,000 generated 2D floorplans.

**Superior Production Solution (verified 2026-08-01)**: Raster2Seq.
**Raster2Seq official github**: https://github.com/Cornell-VAILab/Raster2Seq
**Raster2Seq paper**: https://arxiv.org/abs/2602.09016  
**Raster2Seq website**: https://cornell-vailab.github.io/Raster2Seq/  
**Raster2Seq weights**: https://huggingface.co/haopt/Raster2Seq

#### Core Reconstruction Pipeline (Raster2Seq)

1. **Input Normalization**
   - Image → direct to Raster2Seq.

2. **Core Reconstruction Engine**  
- **Model**: Raster2Seq.
- Primary checkpoint: CubiCasa5K-trained (`cubicasa5k` key on https://huggingface.co/haopt/Raster2Seq).  

3. **2D View (Konva.js)**  
- Structured HTML5 directly from the Raster2Seq polygon sequences.
- 2D View (Konva.js)Reads the JSON. Renders a simple Rect at (x, y). Very fast, no 3D overhead.
- Layer 1 (Grid): Static background.
- Layer 2 (Walls): Lines and Paths (using Konva.Line).
- Layer 3 (Furniture): Konva.Image nodes representing the cabinets top-down.
- Logic: When user drops a cabinet, save its { x, y, rotation, sku_id } to React State.

4. Database (Neon) - The Single Source of Truth:
- Stores JSON metadata + URLs to GLB files (on CDN).
- Neon Postgres database stores a JSON "Scene State" describing the room:
- { "cabinets": [ { "id": "cab_001", "x": 10, "y": 0, "model_url": "cdn.site.com/cab.glb" } ] }

5. CDN (S3/R2): Store the GLB files on a CDN. 
- Store only the URL (e.g., https://cdn.yoursite.com/cabinet_01.glb) in Neon.
- Result: The browser downloads the model directly from the edge server (CDN) in parallel, bypassing your backend entirely.

5. **3D View (Three.js)**  
- Listens to the same React State.
- When visible, it iterates the state and loads the corresponding GLB files for each sku_id.
- User clicks "3D". Three.js initializes. It iterates through the same JSON list.
- Optimization: It uses InstancedMesh. If the user has 20 identical "Base Cabinet" units, Three.js loads the GLB once and draws it 20 times at zero extra GPU cost.
- Uses GLTFLoader combined with Draco Compression (a small Wasm decoder). This reduces your cabinet file size by ~40% and decodes it on a background thread.
- Best for "interchangeable views" because it can spin up/down in milliseconds.
- Strong complementary viewer: https://github.com/laanlabs/openPlan3D (SvelteKit + Three.js, open-source 2D/3D floor-plan editor).

**Libraries / Frameworks the model must call (exact sequence)**:
1. Raster2Seq inference (official code from https://github.com/Cornell-VAILab/Raster2Seq + checkpoint from https://huggingface.co/haopt/Raster2Seq).  
2. Write structured layout JSON (polygons + semantics + scale) to Postgres.  

# 3.2 Task Sequence 2 — `optimize_kitchen` (Finishes + Inspiration → Complete System)

## Sub-sequence
* **(2-a)** (i) User submits cabinet finishes (UI wizard-to-catlog) + (ii) User's multi-modal input of design aspiration/goals.  
* **(2-b)** Solver ingests User's multi-modal design aspiration + goals (2-a-ii)  → 3D Viewer outputs full results.

## Production Leader for Extreme Token Efficiency Catalog Mapping
* **Hexaly Product Solvers**: Native C++ core + full API.
* **Google OR-Tools CP-SAT**: fallback solver. 

## Model Task Matrix for (2-b)
* **Plan**: Grok-4.5 (layout-aware planning + storage reasoning).  
* **Review / Test**: Lightweight constrained checker (C++ or Python tool) + Grok-4.5 for aesthetic judgment.  
* **Code / Implement**: The optimizer + placement emitter (deterministic code, not LLM generation of geometry).  
* **Generation assist**: Cosmos 3 Nano or 4-Step distilled variants.

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

## 5. Precise Implementation Phases

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

1. **Upload floorplan** (multi-modal user input) in Open WebUI → agent → `parse_and_map_floorplan` (Raster2Seq primary engine) → layout written to Postgres + 2D viewer updated → 3D auto-derived. 2D+3D viewers interactive and editable.
2. **Select finishes + upload inspiration** → agent → catalog retrieval + → constraint verification against the *Raster2Seq-reconstructed* layout → complete placement list.  
3. **One-shot render** of the verified system in the Three.js / openPlan3D viewer.  
4. **Iterative refinement** via Grok-4.5 + constrained tools.  
5. **Background autonomous exploration** runs entirely against the C++ runtime.

---

## 7. Production Readiness Checklist

- [ ] Raster2Seq pipeline produces identical geometry for identical inputs.  
- [ ] E2E tests cover the full critical path.  

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
