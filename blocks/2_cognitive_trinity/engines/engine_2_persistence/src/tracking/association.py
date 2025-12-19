# Engine 2: Detection-to-Track Association
# Hungarian algorithm for optimal matching

from typing import List, Dict, Tuple
import numpy as np


def compute_iou_matrix(bboxes_a: List, bboxes_b: List) -> np.ndarray:
    """
    Compute IoU matrix between two sets of bounding boxes.
    
    Args:
        bboxes_a: First set of bboxes [N, 4]
        bboxes_b: Second set of bboxes [M, 4]
        
    Returns:
        IoU matrix [N, M]
    """
    if len(bboxes_a) == 0 or len(bboxes_b) == 0:
        return np.zeros((len(bboxes_a), len(bboxes_b)))
    
    # TODO: Implement actual IoU computation
    return np.random.rand(len(bboxes_a), len(bboxes_b))


def compute_cosine_distance(features_a: np.ndarray, features_b: np.ndarray) -> np.ndarray:
    """
    Compute cosine distance matrix between feature sets.
    
    Args:
        features_a: [N, D] feature matrix
        features_b: [M, D] feature matrix
        
    Returns:
        Distance matrix [N, M] where 0=identical, 1=orthogonal
    """
    if len(features_a) == 0 or len(features_b) == 0:
        return np.zeros((len(features_a), len(features_b)))
    
    # Normalize features
    a_norm = features_a / (np.linalg.norm(features_a, axis=1, keepdims=True) + 1e-8)
    b_norm = features_b / (np.linalg.norm(features_b, axis=1, keepdims=True) + 1e-8)
    
    # Cosine similarity -> distance
    similarity = np.dot(a_norm, b_norm.T)
    distance = 1.0 - similarity
    
    return distance


def hungarian_matching(cost_matrix: np.ndarray, threshold: float) -> Tuple[Dict, List, List]:
    """
    Hungarian algorithm for optimal bipartite matching.
    
    Args:
        cost_matrix: [N, M] cost matrix (lower = better)
        threshold: Maximum cost to accept match
        
    Returns:
        matched: Dict[det_idx -> track_idx]
        unmatched_dets: List of unmatched detection indices
        unmatched_tracks: List of unmatched track indices
    """
    # TODO: Implement using scipy.optimize.linear_sum_assignment
    matched = {}
    unmatched_dets = list(range(cost_matrix.shape[0]))
    unmatched_tracks = list(range(cost_matrix.shape[1]))
    
    return matched, unmatched_dets, unmatched_tracks


def associate_detections(
    detections: List,
    tracks: List,
    features_det: np.ndarray,
    features_track: np.ndarray,
    iou_threshold: float = 0.3,
    reid_threshold: float = 0.4
) -> Tuple[Dict, List, List]:
    """
    Two-stage association: IoU then ReID.
    
    Args:
        detections: Current frame detections
        tracks: Existing tracks
        features_det: Detection embeddings
        features_track: Track embeddings
        iou_threshold: IoU matching threshold
        reid_threshold: ReID matching threshold
        
    Returns:
        matched, unmatched_dets, unmatched_tracks
    """
    if len(tracks) == 0:
        return {}, list(range(len(detections))), []
    
    if len(detections) == 0:
        return {}, [], list(range(len(tracks)))
    
    # Stage 1: IoU matching
    iou_matrix = compute_iou_matrix(detections, tracks)
    cost_iou = 1.0 - iou_matrix
    matched_iou, unmatched_dets, unmatched_tracks = hungarian_matching(cost_iou, 1.0 - iou_threshold)
    
    # Stage 2: ReID matching for remaining
    if len(unmatched_dets) > 0 and len(unmatched_tracks) > 0:
        feat_det_remaining = features_det[unmatched_dets]
        feat_track_remaining = features_track[unmatched_tracks]
        
        cost_reid = compute_cosine_distance(feat_det_remaining, feat_track_remaining)
        matched_reid, still_unmatched_dets, still_unmatched_tracks = hungarian_matching(cost_reid, reid_threshold)
        
        # Merge results
        for det_idx, track_idx in matched_reid.items():
            matched_iou[unmatched_dets[det_idx]] = unmatched_tracks[track_idx]
        
        unmatched_dets = [unmatched_dets[i] for i in still_unmatched_dets]
        unmatched_tracks = [unmatched_tracks[i] for i in still_unmatched_tracks]
    
    return matched_iou, unmatched_dets, unmatched_tracks
