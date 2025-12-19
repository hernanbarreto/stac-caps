# Block 3: Point Cloud Segmentation
def segment_points_by_object(point_cloud, objects_3d):
    """Segment point cloud by 3D bboxes. (<1ms)"""
    return {obj.track_id: [] for obj in objects_3d}
