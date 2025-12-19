# Block 3: Fusion - Traceability Matrix

## Mapeo Arquitectura → Código
| ID SVG | Componente | Archivo | Clase/Función |
|--------|------------|---------|---------------|
| comp_projection | Depth-to-3D | projection/depth_to_3d.py | project_bbox_to_3d() |
| comp_smpl | SMPL Placer | smpl/placer.py | place_smpl_avatar() |
| comp_ply | PLY Aligner | ply/aligner.py | align_ply_wireframe() |
| comp_segment | Segmentation | segmentation/point_cloud.py | segment_points_by_object() |
| comp_smooth | Temporal | smoothing/temporal.py | smooth_positions() |

## Estructura
```
3_fusion/src/
├── fusion.py, interfaces.py, config.py
├── projection/, smpl/, ply/, segmentation/, smoothing/
```

| Fecha | Cambio |
|-------|--------|
| 2025-12-19 | Creación inicial |
