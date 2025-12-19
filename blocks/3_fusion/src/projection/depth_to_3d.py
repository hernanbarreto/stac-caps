# Block 3: Depth-to-3D Projection
def project_bbox_to_3d(bbox2D, depth_map, intrinsics):
    """Project 2D bbox to 3D using depth. (<1ms)"""
    x1, y1, x2, y2 = bbox2D
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    depth = 10.0  # Placeholder
    fx, fy = 500, 500
    X = (cx - 960) * depth / fx
    Y = (cy - 540) * depth / fy
    Z = depth
    w3d = (x2 - x1) * depth / fx
    h3d = (y2 - y1) * depth / fy
    return (X, Y, Z, w3d, h3d, 1.0)
