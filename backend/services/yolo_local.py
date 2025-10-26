import base64
import logging
from io import BytesIO
from PIL import Image
import numpy as np
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

MATERIAL_CLASSES = [
    'brick', 'carpet', 'ceramic', 'fabric', 'foliage', 'food', 'glass', 'hair', 
    'leather', 'metal', 'mirror', 'other', 'painted', 'paper', 'plastic', 
    'polished_stone', 'skin', 'sky', 'stone', 'tile', 'wallpaper', 'water', 'wood'
]

class LocalYOLOModel:
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.class_names = MATERIAL_CLASSES
        
    def load_model(self):
        try:
            from ultralytics import YOLO
            logger.info("Loading custom YOLOv8 material detection model...")
            self.model = YOLO('model/weights/material_classifier_best.pt')
            
            model_classes = self.model.names
            if isinstance(model_classes, dict):
                model_class_list = [model_classes[i] for i in sorted(model_classes.keys())]
            else:
                model_class_list = list(model_classes)
            
            logger.info(f"Model has {len(model_class_list)} classes: {model_class_list}")
            
            if 'person' in model_class_list or 'car' in model_class_list:
                logger.warning("WARNING: Model appears to have COCO classes instead of materials!")
                logger.warning("Expected material classes, but found COCO classes.")
                logger.warning("Using predefined material classes instead.")
                self.class_names = MATERIAL_CLASSES
            else:
                logger.info("Using model's trained material classes")
                self.class_names = model_classes
            
            self.model_loaded = True
            logger.info(f"Material detection model ready with {len(self.class_names)} material classes")
            return True
        except ImportError:
            logger.error("Ultralytics not installed. Run: pip install ultralytics")
            return False
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            return False
    
    def segment_frame(self, frame_data: str) -> Optional[Dict[str, Any]]:
        if not self.model_loaded:
            if not self.load_model():
                return self._mock_segmentation()
        
        try:
            image_bytes = base64.b64decode(frame_data.split(',')[1] if ',' in frame_data else frame_data)
            image = Image.open(BytesIO(image_bytes))
            
            results = self.model(image, verbose=False, conf=0.25)
            
            segments = []
            if hasattr(results[0], 'boxes') and results[0].boxes is not None:
                for i, box in enumerate(results[0].boxes.data):
                    x1, y1, x2, y2, conf, cls = box.cpu().numpy()
                    class_id = int(cls)
                    class_name = self.class_names[class_id] if class_id < len(self.class_names) else f'unknown-{class_id}'
                    
                    segments.append({
                        'id': i,
                        'bbox': [int(x1), int(y1), int(x2 - x1), int(y2 - y1)],
                        'confidence': float(conf),
                        'class': class_id,
                        'class_name': class_name,
                        'area': int((x2 - x1) * (y2 - y1)),
                        'mask': []
                    })
            
            if len(segments) > 0:
                logger.info(f"✨ Detected {len(segments)} material(s):")
                for seg in segments:
                    material = seg['class_name'].upper()
                    confidence = seg['confidence']
                    area = seg['area']
                    logger.info(f"  🎯 {material} (confidence: {confidence:.2f}, area: {area}px)")
            else:
                logger.warning(f"⚠️  No materials detected in frame")
            
            return {
                'segments': segments,
                'count': len(segments),
                'success': True
            }
            
        except Exception as e:
            logger.error(f"YOLO inference failed: {e}")
            return self._mock_segmentation()
    
    def _mock_segmentation(self) -> Dict[str, Any]:
        logger.warning("Using mock segmentation (model not available)")
        
        segments = [
            {'id': 0, 'bbox': [100, 100, 200, 150], 'confidence': 0.85, 'area': 30000, 'class': 22, 'class_name': 'wood'},
            {'id': 1, 'bbox': [320, 100, 180, 160], 'confidence': 0.78, 'area': 28800, 'class': 9, 'class_name': 'metal'},
            {'id': 2, 'bbox': [100, 280, 190, 140], 'confidence': 0.92, 'area': 26600, 'class': 6, 'class_name': 'glass'},
        ]
        
        logger.info(f"✨ Mock detection: {len(segments)} material(s)")
        
        return {
            'segments': segments,
            'count': len(segments),
            'success': True,
            'mock': True
        }

local_yolo = LocalYOLOModel()

