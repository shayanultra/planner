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
