## 6. Full User Flow Mapping

1. **Upload floorplan** (multi-modal user input) in Open WebUI → agent → `parse_and_map_floorplan` (Raster2Seq primary engine) → layout written to Postgres + 2D viewer updated → 3D auto-derived. 2D+3D viewers interactive and editable.
2. **Select finishes + upload inspiration** → agent → catalog retrieval + → constraint verification against the *Raster2Seq-reconstructed* layout → complete placement list.  
3. **One-shot render** of the verified system in the Three.js / openPlan3D viewer.  
4. **Iterative refinement** via Grok-4.5 + constrained tools.  
5. **Background autonomous exploration** runs entirely against the C++ runtime.
