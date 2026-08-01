# Kitchen Planner AI

High-volume, utility-first kitchen planning: accurate floorplan reconstruction first, then catalog-constrained kitchen systems. Domain language for the Version 3 blueprint (`docs/goal.md`).

## Language

### Space reconstruction

**Layout**:
The authoritative geometric and semantic record of a reconstructed floorplan (polygons, labels, scale).
_Avoid_: floorplan model, scene, map (when meaning the stored reconstruction)

**Polygon Sequence**:
Ordered, labeled polygons (rooms, doors, windows) produced by Raster2Seq for a single Layout.
_Avoid_: vectorization, CAD drawing, mesh

**Scale Factor**:
Recoverable metric multiplier stored on a Layout so image-space polygons map to real-world dimensions.
_Avoid_: resolution, DPI (unless discussing raster input only)

**2D Representation**:
SVG or canvas geometry generated directly from a Layout's polygons; the user-facing authority for geometry edits.
_Avoid_: floorplan image, raster, screenshot

**3D Extrusion**:
Deterministic vertical extrusion of a verified 2D Representation into a scene graph; never an independent generative reconstruction.
_Avoid_: 3D reconstruction, lift, HouseCrafter (reserved for later optional enhancement)

### Planning & catalog

**Kitchen System**:
A complete, catalog-compliant placement of cabinets and appliances constrained to a Layout.
_Avoid_: design, render, scene (when meaning the product placement result)

**Cabinet**:
A catalog product SKU with type (base / wall / tall), size variants, and optional aesthetic embedding.
_Avoid_: unit, module (unless referring to software modules)

**Finish**:
A user-selected material/color constraint applied when retrieving and ranking Cabinets.
_Avoid_: style, theme, palette (when meaning the catalog-bound selection)

**Inspiration**:
User-uploaded image(s) used only to produce an aesthetic embedding for ranking, not for free-form geometry generation.
_Avoid_: mood board, reference (when meaning the aesthetic input)

### Runtime & sessions

**Agent Runtime**:
The single-process C++ loop (llama.cpp + agent extensions) that owns high-volume autonomous work and tool dispatch.
_Avoid_: multi-agent graph, orchestrator swarm, portal backend (for loops)

**Portal**:
The Open WebUI (SvelteKit) user surface for chat, uploads, and the 2D/3D viewer; never on the high-volume autonomous path.
_Avoid_: frontend, dashboard, app (when meaning this surface)

**Session**:
Persisted interactive planning state for a user engagement (layout id, finishes, inspiration refs, placement drafts).
_Avoid_: conversation only, chat thread (Session may outlive a single chat)

**Audit Log**:
Append-only record of tool calls, routing decisions, and material mutations for observability and cost control.
_Avoid_: debug log, telemetry (when meaning the durable audit trail)

### Intelligence routing (roles, not products)

**Reconstruction Path**:
Input normalization → Raster2Seq → optional light polish → Layout write; sole path for floorplan geometry.
_Avoid_: CubiCasa5K+OpenCV primary, hybrid primary engines

**Planning Path**:
Interactive chat, refinement, and storage reasoning routed to Grok-4.5.
_Avoid_: using generative models to invent wall geometry

**Synthesis Path**:
Optional high-fidelity visual assist via Cosmos after deterministic placement is locked.
_Avoid_: one-shot generative kitchen geometry as the primary optimizer

## Relationships

- A **Layout** is produced only via the **Reconstruction Path** and owns one **Polygon Sequence** plus a **Scale Factor**.
- A **2D Representation** is derived from a **Layout**; a **3D Extrusion** is derived only from a verified **2D Representation**.
- A **Session** references at most one active **Layout** and zero or more **Finish** selections and **Inspiration** inputs.
- A **Kitchen System** is constrained hard to a **Layout** and soft-ranked by **Inspiration** aesthetic embeddings against **Cabinet** catalog vectors.
- The **Agent Runtime** executes high-volume loops; the **Portal** never participates in those loops.
- Every material tool call and routing decision appends to the **Audit Log**.

## Example dialogue

> **Dev:** "User uploaded a PDF floorplan — do we send that to Grok to invent walls?"
> **Domain expert:** "No. PDF goes through Poppler to a raster, then the **Reconstruction Path** (Raster2Seq) writes a **Layout**. Grok is only for text-structured assist or later **Planning Path** refinement."
>
> **Dev:** "Can the **3D Extrusion** disagree with the **2D Representation** if Cosmos looks better?"
> **Domain expert:** "Never. **3D Extrusion** is deterministic from verified 2D. Cosmos is **Synthesis Path** only after placement is locked — optional visuals, not geometry authority."
>
> **Dev:** "Should autonomous redesign loops hit Open WebUI for speed?"
> **Domain expert:** "No. Those stay inside the **Agent Runtime**. The **Portal** is interactive only."

## Flagged ambiguities

- "floorplan" in casual speech may mean the input image/PDF or the stored **Layout** — prefer **Layout** for the stored reconstruction and "floorplan input" for the upload.
- "map" is overloaded (wayfinder map vs floorplan) — use **Layout** for geometry; "wayfinder map" for effort planning under `.scratch/`.
- "agent" alone is ambiguous — use **Agent Runtime** for the C++ loop; do not imply multi-agent graphs on the critical path.
- Catalog seeding and embeddings are Phase 1 data-plane concerns but **not** part of Slice A (`parse_and_map_floorplan`).
