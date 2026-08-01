# Raster2Seq is the sole primary floorplan engine

Version 3 fully replaces CubiCasa5K+OpenCV (and any hybrid primary path) with Raster2Seq as the only production polygon extraction engine for `parse_and_map_floorplan`. Optional light Douglas-Peucker / area filter may polish polygons but must not replace Raster2Seq. Text/PDF assist via Grok or Cosmos Reasoner is limited to input normalization, never primary geometry extraction.

**Status:** accepted

## Considered options

- CubiCasa5K detector + classical OpenCV vectorization (v1/v2) — rejected: weaker Room/Corner F1 and multi-stage brittleness on complex plans.
- Hybrid multi-engine primary path — rejected: non-determinism and dual maintenance without meeting the foundation requirement.
- Raster2Seq sole primary — accepted: SOTA labeled polygon sequences (SIGGRAPH 2026), direct fit for 2D SVG + deterministic 3D extrusion.

## Consequences

- All Layout writes must originate from Raster2Seq (or user correction of Raster2Seq output), not generative models.
- Checkpoint path and inference entrypoints are documented against the vendored `Raster2Seq/` tree and `haopt/Raster2Seq` weights.
