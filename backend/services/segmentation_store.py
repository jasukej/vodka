import threading
from typing import Dict, Any, Optional
import time
import logging

logger = logging.getLogger(__name__)

class SegmentationStore:
    def __init__(self):
        self._segments = None
        self._timestamp = None
        self._lock = threading.Lock()
        
    def store_segments(self, segments: Dict[str, Any], timestamp: float = None) -> None:
        with self._lock:
            self._segments = segments
            self._timestamp = timestamp or time.time()
            logger.info(f"Stored {segments.get('count', 0)} segments at timestamp {self._timestamp}")
    
    def get_segments(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._segments
    
    def get_timestamp(self) -> Optional[float]:
        with self._lock:
            return self._timestamp
    
    def is_calibrated(self) -> bool:
        with self._lock:
            if self._segments is None:
                return False
            segments = self._segments.get('segments', [])
            return len(segments) > 0
    
    def clear(self) -> None:
        with self._lock:
            self._segments = None
            self._timestamp = None
            logger.info("Cleared segmentation store")
    
    def get_segment_count(self) -> int:
        with self._lock:
            if self._segments is None:
                return 0
            return len(self._segments.get('segments', []))

segmentation_store = SegmentationStore()

