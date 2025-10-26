import base64
import logging
import os
from io import BytesIO
from PIL import Image
import numpy as np
from typing import Dict, Any, Optional, List
from ultralytics import YOLO

logger = logging.getLogger(__name__)

class DrumstickDetector:
    def __init__(self, model_size=Config.DRUMSTICK_MODEL_SIZE):
        self.model = None
        self.model_loaded = False
        self.class_names = ['drumstick']  # Custom trained model classes
        self.model_size = model_size 
        self.pretrained_model = None
        
    def load_model(self):
        try:
            logger.info("Loading drumstick detection model...")
            
            # First try custom trained model
            custom_model_paths = [
                'model/drumsticks/data/best.pt',
                '../model/drumsticks/data/best.pt',
                '../../model/drumsticks/data/best.pt'
            ]
            
            model_loaded = False
            for model_path in custom_model_paths:
                if os.path.exists(model_path):
                    self.model = YOLO(model_path)
                    logger.info(f"✅ Custom drumstick model loaded from: {model_path}")
                    model_loaded = True
                    break
            
            # If custom model not found, use pretrained model
            if not model_loaded:
                pretrained_models = {
                    'nano': 'yolov10n.pt',      # Fastest, good accuracy
                    'small': 'yolov10s.pt',     # Better accuracy, still fast
                    'medium': 'yolov10m.pt',    # Even better, medium speed
                    'large': 'yolov10l.pt',     # High accuracy, slower
                    'xlarge': 'yolov10x.pt',    # Best accuracy, slowest
                    'auto': 'yolov10n.pt'       # Default to nano for speed
                }
                
                model_name = pretrained_models.get(self.model_size, 'yolov10n.pt')
                logger.info(f"⚠️  Custom model not found, using pretrained {model_name}")
                logger.info("   YOLOv10 is ~3x faster than YOLOv8 with better accuracy")
                self.model = YOLO(model_name)  # Auto-downloads if needed
                self.pretrained_model = model_name
                model_loaded = True
            
            self.class_names = self.model.names
            self.model_loaded = True
            logger.info(f"✅ Model loaded with {len(self.class_names)} classes")
            logger.info(f"   Classes: {list(self.class_names.values())}")
            return True
        except ImportError:
            logger.error("Ultralytics not installed. Run: pip install ultralytics")
            return False
        except Exception as e:
            logger.error(f"Failed to load drumstick detection model: {e}")
            return False
    
    
    def detect_drumsticks(self, frame_data: str, confidence_threshold: float = 0.15) -> Optional[Dict[str, Any]]:
        if not self.model_loaded:
            if not self.load_model():
                logger.error("CRITICAL: Cannot load drumstick detection model - aborting detection")
                return None
        
        # Generate unique detection ID for debugging
        import time
        detection_id = f"{int(time.time() * 1000)}"
        
        try:
            logger.info(f"🥢 Running YOLOv8nano inference on frame... (ID: {detection_id})")
            image_bytes = base64.b64decode(frame_data.split(',')[1] if ',' in frame_data else frame_data)
            image = Image.open(BytesIO(image_bytes))
            
            # Debug: Log frame info
            frame_hash = hash(frame_data) % 1000000
            logger.info(f"🥢 Frame info: size={len(frame_data)} bytes, hash={frame_hash}, image_size=({image.width}x{image.height})")
            
            logger.info(f"🥢 Model inference starting with confidence threshold: {confidence_threshold} (ID: {detection_id})")
            results = self.model(image, verbose=False, conf=confidence_threshold)
            logger.info(f"🥢 Model inference completed (ID: {detection_id})")
            
            detections = []
            if hasattr(results[0], 'boxes') and results[0].boxes is not None:
                for i, box in enumerate(results[0].boxes.data):
                    x1, y1, x2, y2, conf, cls = box.cpu().numpy()
                    class_id = int(cls)
                    class_name = self.class_names[class_id] if class_id < len(self.class_names) else f'unknown-{class_id}'
                    
                    detections.append({
                        'id': i,
                        'bbox': [int(x1), int(y1), int(x2 - x1), int(y2 - y1)],
                        'confidence': float(conf),
                        'class': class_id,
                        'class_name': class_name,
                        'area': int((x2 - x1) * (y2 - y1)),
                        'center': {
                            'x': int(x1 + (x2 - x1) / 2),
                            'y': int(y1 + (y2 - y1) / 2)
                        }
                    })
            
            if len(detections) > 0:
                logger.info(f"🥢 YOLOv8nano detected {len(detections)} drumstick(s):")
                for det in detections:
                    logger.info(f"  - {det['class_name'].upper()} (conf: {det['confidence']:.2f}) at ({det['center']['x']}, {det['center']['y']})")
            else:
                logger.info("🥢 YOLOv8nano detected NO drumsticks in frame")
            
            return {
                'detections': detections,
                'count': len(detections),
                'success': True,
                'image_size': [image.width, image.height],
                'model_inference': True
            }
            
        except Exception as e:
            logger.error(f"CRITICAL: YOLOv8nano inference failed: {e}")
            logger.error("Aborting drumstick detection - no fallback to mock data")
            return None
    
    def get_best_drumstick_position(self, frame_data: str, confidence_threshold: float = 0.15) -> Optional[Dict[str, float]]:
        detection_result = self.detect_drumsticks(frame_data, confidence_threshold)
        
        if not detection_result or not detection_result.get('success'):
            logger.warning("No valid drumstick detection result - returning None")
            return None
        
        # Ensure this is from actual model inference, not mock data
        if not detection_result.get('model_inference', False):
            logger.error("CRITICAL: Detection result is not from model inference - rejecting")
            return None
        
        detections = detection_result.get('detections', [])
        if not detections:
            logger.info("YOLOv8nano detected no drumsticks - returning None")
            return None
        
        best_detection = max(detections, key=lambda d: d['confidence'])
        logger.info(f"🥢 Best drumstick detection: {best_detection['class_name']} at ({best_detection['center']['x']}, {best_detection['center']['y']}) with confidence {best_detection['confidence']:.2f}")
        
        return {
            'x': float(best_detection['center']['x']),
            'y': float(best_detection['center']['y']),
            'confidence': best_detection['confidence'],
            'class_name': best_detection['class_name']
        }
    
    def _mock_detection(self) -> Dict[str, Any]:
        logger.warning("Using mock drumstick detection (model not available)")
        
        detections = [
            {
                'id': 0, 
                'bbox': [200, 150, 50, 200], 
                'confidence': 0.85, 
                'area': 10000, 
                'class': 0, 
                'class_name': 'drumstick',
                'center': {'x': 225, 'y': 250}
            }
        ]
        
        return {
            'detections': detections,
            'count': len(detections),
            'success': True,
            'mock': True,
            'image_size': [640, 480]
        }

# Initialize with config from Config class
from config import Config
drumstick_detector = DrumstickDetector(model_size=Config.DRUMSTICK_MODEL_SIZE)
