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

## Core Reconstruction Pipeline (Raster2Seq)

1. **Input Normalization**
   * Image → direct to Raster2Seq.
2. **Core Reconstruction Engine**  
   * **Model**: Raster2Seq.
   * **Primary checkpoint**: CubiCasa5K-trained (`cubicasa5k` key on HF).  
3. **2D View (Konva.js)**  
   * Structured HTML5 directly from the Raster2Seq polygon sequences.
   * Renders a simple Rect at (x, y) via Konva.Line and Konva.Image nodes. Very fast, no 3D overhead.
4. **Database (Neon) - The Single Source of Truth**
   * Stores JSON metadata + URLs to GLB files (on CDN).
5. **CDN (S3/R2)**
   * Store only the URL in Neon. The browser downloads the model directly from the edge server in parallel.
6. **3D View (Three.js)**  
   * Iterates through the same JSON list via InstancedMesh to draw identical units at zero extra GPU cost.
   * Uses GLTFLoader combined with Draco Compression.

## Mandatory Execution Order:
1. Raster2Seq inference.  
2. Write structured layout JSON (polygons + semantics + scale) to Postgres.

