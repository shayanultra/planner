## 5. Precise System Implementation

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

