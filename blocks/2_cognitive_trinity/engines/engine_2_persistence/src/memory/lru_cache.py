# Engine 2: LRU Track Memory
# Least Recently Updated cache for track storage

from typing import Dict, Optional, List
from collections import OrderedDict
from ..interfaces import Track, TrackState


class TrackMemory:
    """
    LRU cache for track storage with automatic eviction.
    
    Max Size: 50 tracks
    Eviction Policy: Lowest quality_score among oldest
    Memory per Track: ~100KB (history + embeddings)
    """
    
    def __init__(self, max_size: int = 50):
        self.max_size = max_size
        self.tracks: OrderedDict[int, Track] = OrderedDict()
    
    def get(self, track_id: int) -> Optional[Track]:
        """
        Get track by ID, marking as recently used.
        
        Args:
            track_id: Track identifier
            
        Returns:
            Track or None if not found
        """
        if track_id in self.tracks:
            # Move to end (most recently used)
            self.tracks.move_to_end(track_id)
            return self.tracks[track_id]
        return None
    
    def put(self, track: Track):
        """
        Add or update track in cache.
        
        Args:
            track: Track to store
        """
        track_id = track.track_id
        
        if track_id in self.tracks:
            # Update existing
            self.tracks[track_id] = track
            self.tracks.move_to_end(track_id)
        else:
            # Check capacity
            if len(self.tracks) >= self.max_size:
                self._evict()
            
            # Add new
            self.tracks[track_id] = track
    
    def remove(self, track_id: int):
        """Remove track from cache."""
        if track_id in self.tracks:
            del self.tracks[track_id]
    
    def _evict(self):
        """
        Evict track with lowest quality_score among oldest.
        """
        if not self.tracks:
            return
        
        # Find candidates (first half = oldest)
        candidates = list(self.tracks.items())[:len(self.tracks) // 2 + 1]
        
        if not candidates:
            # Fall back to first item
            first_key = next(iter(self.tracks))
            del self.tracks[first_key]
            return
        
        # Find lowest quality
        min_quality = float('inf')
        evict_id = candidates[0][0]
        
        for track_id, track in candidates:
            if track.quality_score < min_quality:
                min_quality = track.quality_score
                evict_id = track_id
        
        del self.tracks[evict_id]
    
    def get_all(self) -> List[Track]:
        """Get all tracks."""
        return list(self.tracks.values())
    
    def get_active(self) -> List[Track]:
        """Get only active (non-deleted) tracks."""
        return [t for t in self.tracks.values() 
                if t.state != TrackState.DELETED]
    
    def count(self) -> int:
        """Get number of tracks in cache."""
        return len(self.tracks)
    
    def clear(self):
        """Clear all tracks."""
        self.tracks.clear()
