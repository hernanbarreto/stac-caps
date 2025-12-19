"""
STAC-CAPS Video Processor
Frame-by-frame video processing with annotated output
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Generator, Tuple, Optional, Dict
import time

from .pipeline import Pipeline


class VideoProcessor:
    """
    Process video files frame by frame.
    
    Features:
    - Efficient frame extraction
    - Pipeline integration
    - Annotated output video
    - Progress tracking
    """
    
    def __init__(self, video_path: str):
        self.video_path = Path(video_path)
        self.cap = None
        self.info = self._get_video_info()
    
    def _get_video_info(self) -> Dict:
        """Get video metadata."""
        cap = cv2.VideoCapture(str(self.video_path))
        
        info = {
            "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            "fps": cap.get(cv2.CAP_PROP_FPS),
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            "resolution": (
                int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            )
        }
        
        cap.release()
        return info
    
    def extract_first_frame(self, output_path: str) -> Dict:
        """Extract and save first frame for calibration."""
        cap = cv2.VideoCapture(str(self.video_path))
        
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError("Could not read video")
        
        cv2.imwrite(output_path, frame)
        cap.release()
        
        return self.info
    
    def iter_frames(self) -> Generator[Tuple[int, np.ndarray], None, None]:
        """Iterate through all frames."""
        cap = cv2.VideoCapture(str(self.video_path))
        
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            yield frame_idx, frame_rgb
            frame_idx += 1
        
        cap.release()
    
    def process_with_pipeline(
        self,
        pipeline: Pipeline,
        output_path: Optional[str] = None,
        skip_frames: int = 0
    ) -> Generator[Tuple[int, np.ndarray, np.ndarray], None, None]:
        """
        Process video through STAC-CAPS pipeline.
        
        Args:
            pipeline: Configured Pipeline instance
            output_path: Path for annotated output video
            skip_frames: Skip every N frames (for speed)
            
        Yields:
            (frame_idx, original_frame, annotated_frame)
        """
        cap = cv2.VideoCapture(str(self.video_path))
        writer = None
        
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(
                output_path,
                fourcc,
                self.info["fps"],
                self.info["resolution"]
            )
        
        frame_idx = 0
        process_times = []
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Skip frames if requested
                if skip_frames > 0 and frame_idx % (skip_frames + 1) != 0:
                    frame_idx += 1
                    continue
                
                # Convert BGR to RGB for processing
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process through pipeline
                start_time = time.time()
                result = pipeline.process_frame(frame_rgb, frame_idx)
                process_time = time.time() - start_time
                process_times.append(process_time)
                
                # Annotate frame
                annotated = self._annotate_frame(frame, result)
                
                # Write to output
                if writer:
                    writer.write(annotated)
                
                yield frame_idx, frame_rgb, annotated
                frame_idx += 1
        
        finally:
            cap.release()
            if writer:
                writer.release()
            
            # Report stats
            if process_times:
                avg_time = np.mean(process_times) * 1000
                avg_fps = 1.0 / np.mean(process_times)
                print(f"Average processing time: {avg_time:.1f}ms ({avg_fps:.1f} FPS)")
    
    def _annotate_frame(self, frame: np.ndarray, result: Dict) -> np.ndarray:
        """
        Annotate frame with detections, tracks, and alerts.
        
        Args:
            frame: Original BGR frame
            result: Pipeline result dict
            
        Returns:
            Annotated BGR frame
        """
        annotated = frame.copy()
        
        # Draw detections
        for det in result.get("detections", []):
            x1, y1, x2, y2 = det.get("bbox", [0, 0, 0, 0])
            category = det.get("category", "UNKNOWN")
            conf = det.get("confidence", 0)
            
            # Color by category
            colors = {
                "PERSON": (0, 0, 255),    # Red
                "KNOWN": (0, 255, 0),     # Green
                "UNKNOWN": (255, 165, 0)  # Orange
            }
            color = colors.get(category, (255, 255, 255))
            
            cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            label = f"{category} {conf:.2f}"
            cv2.putText(annotated, label, (int(x1), int(y1) - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Draw tracks with IDs
        for track in result.get("tracks", []):
            track_id = track.get("track_id", 0)
            x1, y1, x2, y2 = track.get("bbox", [0, 0, 0, 0])
            
            cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 0), 2)
            cv2.putText(annotated, f"ID:{track_id}", (int(x1), int(y2) + 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
        
        # Draw TTC and alert
        ttc = result.get("ttc")
        action = result.get("action", "CLEAR")
        
        # Status bar at top
        status_color = {
            "EMERGENCY": (0, 0, 255),
            "SERVICE": (0, 128, 255),
            "WARNING": (0, 255, 255),
            "CAUTION": (0, 255, 128),
            "CLEAR": (0, 255, 0)
        }.get(action, (255, 255, 255))
        
        cv2.rectangle(annotated, (0, 0), (frame.shape[1], 40), status_color, -1)
        
        ttc_text = f"TTC: {ttc:.1f}s" if ttc and ttc != float('inf') else "TTC: --"
        cv2.putText(annotated, f"{action} | {ttc_text}", (10, 28),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
        
        return annotated
