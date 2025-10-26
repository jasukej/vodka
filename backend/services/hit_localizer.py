import logging
from typing import Dict, Any, Optional, List
import numpy as np
from services.drumstick_detector import drumstick_detector

logger = logging.getLogger(__name__)

class HitLocalizer:
    def __init__(self):
        self.drum_mapping = {
            0: 'snare',
            1: 'kick',
            2: 'hihat',
            3: 'tom',
            4: 'cymbal'
        }
    
    def localize_hit(
        self, 
        frame: Dict[str, Any], 
        segments: Dict[str, Any], 
        hit_timestamp: float,
        hit_position: Optional[Dict[str, float]] = None
    ) -> Optional[Dict[str, Any]]:
        
        if not segments or not segments.get('segments'):
            logger.warning("No segments available for hit localization")
            return None
        
        segment_list = segments.get('segments', [])
        
        if not segment_list:
            logger.warning("Empty segment list")
            return None
        
        # Use YOLOv8nano to detect actual drumstick position
        actual_hit_position = self._get_drumstick_position(frame)
        
        # Always use YOLOv8nano detection - ignore manual position parameter
        position_to_use = actual_hit_position
        
        selected_segment = self._select_segment(segment_list, position_to_use)
        
        if not selected_segment:
            logger.warning("Could not select a segment for hit")
            return None
        
        segment_id = selected_segment.get('id', 0)
        drum_pad = self.drum_mapping.get(segment_id % len(self.drum_mapping), 'snare')
        
        bbox = selected_segment.get('bbox', [0, 0, 0, 0])
        position = {
            'x': bbox[0] + bbox[2] / 2 if len(bbox) >= 4 else 0,
            'y': bbox[1] + bbox[3] / 2 if len(bbox) >= 4 else 0
        }
        
        result = {
            'drum_pad': drum_pad,
            'segment_id': segment_id,
            'position': position,
            'confidence': selected_segment.get('confidence', 0.0),
            'timestamp': hit_timestamp,
            'bbox': bbox,
            'drumstick_position': actual_hit_position
        }
        
        logger.info(f"Hit localized to {drum_pad} (segment {segment_id})")
        if actual_hit_position:
            logger.info(f"🥢 YOLOv8nano detected drumstick at ({actual_hit_position['x']:.0f}, {actual_hit_position['y']:.0f})")
        else:
            logger.warning("🥢 YOLOv8nano detected NO drumstick - using fallback to largest segment")
        return result
    
    def _get_drumstick_position(self, frame: Dict[str, Any]) -> Optional[Dict[str, float]]:
        """Get drumstick position from frame using YOLOv8nano detection"""
        try:
            frame_data = frame.get('frame')  # Frame buffer stores as 'frame', not 'data'
            if not frame_data:
                logger.warning("No frame data available for drumstick detection")
                return None
            
            logger.info("🥢 Running YOLOv8nano inference for hit localization...")
            drumstick_position = drumstick_detector.get_best_drumstick_position(frame_data)
            
            if drumstick_position:
                logger.info(f"🥢 YOLOv8nano inference successful: drumstick at ({drumstick_position['x']:.0f}, {drumstick_position['y']:.0f})")
            else:
                logger.warning("🥢 YOLOv8nano inference returned no drumstick position")
            
            return drumstick_position
            
        except Exception as e:
            logger.error(f"Error in YOLOv8nano drumstick detection: {e}")
            return None
    
    def _select_segment(
        self, 
        segments: List[Dict[str, Any]], 
        hit_position: Optional[Dict[str, float]] = None
    ) -> Optional[Dict[str, Any]]:
        
        if not segments:
            return None
        
        if hit_position and 'x' in hit_position and 'y' in hit_position:
            hit_x = hit_position['x']
            hit_y = hit_position['y']
            
            logger.info(f'   Checking hit position ({hit_x:.0f}, {hit_y:.0f}) against {len(segments)} segments')
            
            for segment in segments:
                bbox = segment.get('bbox', [])
                if len(bbox) >= 4:
                    x, y, w, h = bbox
                    class_name = segment.get('class_name', 'unknown')
                    logger.debug(f'      Segment {segment.get("id")}: {class_name} bbox=({x}, {y}, {w}, {h})')
                    
                    if x <= hit_x <= x + w and y <= hit_y <= y + h:
                        logger.info(f'   ✅ Hit matched {class_name.upper()} segment (ID: {segment.get("id")})')
                        return segment
            
            logger.info(f'   ⚠️  Hit position not inside any segment, using fallback')
        else:
            logger.info(f'   No position provided, using fallback to largest segment')
        
        valid_segments = [s for s in segments if s.get('confidence', 0) > 0.5]
        if not valid_segments:
            valid_segments = segments
        
        largest_segment = max(valid_segments, key=lambda s: s.get('area', 0))
        class_name = largest_segment.get('class_name', 'unknown')
        logger.info(f'   → Fallback to largest segment: {class_name.upper()} (ID: {largest_segment.get("id")})')
        return largest_segment
    
    def set_drum_mapping(self, mapping: Dict[int, str]) -> None:
        self.drum_mapping = mapping
        logger.info(f"Updated drum mapping: {mapping}")

hit_localizer = HitLocalizer()

