# C++ single-process agent loop is primary

High-volume autonomous design iterations run in a single-process C++ Agent Runtime (llama.cpp core + llama-agent / chatllm.cpp-style loop). Controlled parallel tool calls inside that loop are allowed. Multi-agent planner/reviewer/tester/coder graphs are not on the critical path (optional, gated, cost-logged only for rare interactive exhaustive review).

**Status:** accepted

## Considered options

- Multi-agent graph orchestration on every design loop — rejected: literature shows sequential tasks degrade and token cost multiplies 10–15×.
- Python-primary agent loop — rejected for high-volume path: efficiency and KV/prefix caching goals favor C++ runtime; thin Python sidecars only where libraries lack C++ bindings.
- Single-process C++ with controlled parallel tools — accepted: matches Extreme Token Efficiency and keeps loops off the Portal.

## Consequences

- Portal (Open WebUI) is never on the high-volume autonomous path.
- Routing: Reconstruction Path → Raster2Seq; Planning Path → Grok-4.5; Synthesis Path → Cosmos when needed.
