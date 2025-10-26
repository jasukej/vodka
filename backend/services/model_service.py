import requests
import base64
import logging
from typing import Dict, Any, Optional
from config import Config

logger = logging.getLogger(__name__)

class ModelService:
    def __init__(self):
        self.api_url = Config.HOSTED_MODEL_URL
        self.api_key = Config.HOSTED_MODEL_API_KEY
        self.use_hosted = Config.USE_HOSTED_MODEL
        self.local_model = None
        
    def segment_frame(self, frame_data: str) -> Optional[Dict[str, Any]]:
        if not self.use_hosted:
            logger.info("Using local YOLO model")
            return self._use_local_model(frame_data)
            
        if not self.api_url:
            logger.error("HOSTED_MODEL_URL not configured")
            return None
            
        try:
            headers = {
                'Content-Type': 'application/json'
            }
            
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            payload = {
                'image': frame_data,
                'format': 'base64'
            }
            
            logger.info(f"Sending frame to model at {self.api_url}")
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Received segmentation result with {len(result.get('segments', []))} segments")
            
            return self._parse_response(result)
            
        except requests.exceptions.Timeout:
            logger.error("Model API request timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Model API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in segment_frame: {e}")
            return None
    
    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        segments = response.get('segments', [])
        
        parsed_segments = []
        for segment in segments:
            parsed_segment = {
                'id': segment.get('id'),
                'bbox': segment.get('bbox', segment.get('box', [])),
                'mask': segment.get('mask', []),
                'confidence': segment.get('confidence', 0.0),
                'area': segment.get('area', 0)
            }
            parsed_segments.append(parsed_segment)
        
        return {
            'segments': parsed_segments,
            'count': len(parsed_segments),
            'success': True
        }
    
    def _use_local_model(self, frame_data: str) -> Optional[Dict[str, Any]]:
        if self.local_model is None:
            try:
                from services.yolo_local import local_yolo
                self.local_model = local_yolo
                logger.info("Local YOLO model initialized")
            except ImportError as e:
                logger.error(f"Failed to import local YOLO: {e}")
                return None
        
        return self.local_model.segment_frame(frame_data)

model_service = ModelService()

