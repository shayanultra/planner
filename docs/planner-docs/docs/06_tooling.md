## 4. Additional Tooling That Improves the Complete User Flow

**Objective #1**: established libraries improve accuracy, UX, and reconstruction quality beyond the base architecture:

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

**Objective #2**: Additional tooling and libraries are additive and do not replace the core C++ runtime or Open WebUI portal.

