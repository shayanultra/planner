# Portal is Open WebUI; data plane is Postgres/Neon + pgvector

User-facing Portal is Open WebUI (SvelteKit) with an openPlan3D-style / Three.js 2D+3D viewer. Persistent data lives in Postgres 16+ (local or Neon) with pgvector for catalog and aesthetic embeddings. Core tables: layouts, cabinets, finishes, sessions, audit_log.

**Status:** accepted

## Consequences

- No alternate primary portal stack in v3.
- Schema and embeddings are shared by Agent Runtime tools and Portal reads; high-volume writes still go through the runtime/tools, not Portal-side loops.
