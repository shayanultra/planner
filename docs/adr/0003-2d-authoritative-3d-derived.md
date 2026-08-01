# 2D Representation is authoritative; 3D is deterministic extrusion only

User-correctable 2D geometry (SVG/canvas from Layout polygons) is the authority. 3D is always a deterministic extrusion of the verified 2D Representation (walls full height; doors/windows at sill/lintel). Generative 3D lifting is out of the critical path.

**Status:** accepted

## Consequences

- Identical inputs must yield identical Layout geometry (determinism is a production gate).
- Catalog placement and Kitchen System optimization constrain against Layout polygons, never against an independent 3D mesh.
- Viewer work (openPlan3D / Three.js) consumes Layout polygons; it does not invent walls.
