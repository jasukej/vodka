import threading
from collections import deque
from typing import Optional, Dict, Any
import time
import logging

logger = logging.getLogger(__name__)

class FrameBuffer:
    def __init__(self, max_duration: float = 2.0, max_frames: int = 20):
        self._buffer = deque(maxlen=max_frames)
        self._max_duration = max_duration
        self._lock = threading.Lock()
        
    def add_frame(self, frame_data: str, timestamp: float = None) -> None:
        if timestamp is None:
            timestamp = time.time()
            
        with self._lock:
            self._buffer.append({
                'frame': frame_data,
                'timestamp': timestamp
            })
            self._cleanup_old_frames()
    
    def get_latest_frame(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            if not self._buffer:
                return None
            return self._buffer[-1]
    
    def get_frame_at_time(self, target_timestamp: float) -> Optional[Dict[str, Any]]:
        with self._lock:
            if not self._buffer:
                return None
            
            closest_frame = None
            min_diff = float('inf')
            
            for frame_data in self._buffer:
                diff = abs(frame_data['timestamp'] - target_timestamp)
                if diff < min_diff:
                    min_diff = diff
                    closest_frame = frame_data
            
            return closest_frame
    
    def _cleanup_old_frames(self) -> None:
        if not self._buffer:
            return
            
        current_time = time.time()
        cutoff_time = current_time - self._max_duration
        
        while self._buffer and self._buffer[0]['timestamp'] < cutoff_time:
            self._buffer.popleft()
    
    def clear(self) -> None:
        with self._lock:
            self._buffer.clear()
            logger.info("Cleared frame buffer")
    
    def get_buffer_size(self) -> int:
        with self._lock:
            return len(self._buffer)

frame_buffer = FrameBuffer(max_duration=2.0, max_frames=20)

