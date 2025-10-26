import base64
import logging
from io import BytesIO
from PIL import Image
import numpy as np
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
    'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
    'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
    'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
    'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
    'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
    'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
    'toothbrush'
]

class LocalYOLOModel:
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.class_names = COCO_CLASSES
        
    def load_model(self):
        try:
            from ultralytics import YOLO
            logger.info("Loading YOLOv8 model...")
            self.model = YOLO('model/weights/yolov8n.pt')
            self.class_names = self.model.names
            self.model_loaded = True
            logger.info(f"YOLOv8 model loaded with {len(self.class_names)} classes")
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
                logger.info(f"Detected {len(segments)} objects:")
                for seg in segments:
                    logger.info(f"  - {seg['class_name'].upper()} (conf: {seg['confidence']:.2f})")
            else:
                logger.warning(f"No objects detected in frame")
            
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
            {'id': 0, 'bbox': [100, 100, 200, 150], 'confidence': 0.85, 'area': 30000, 'class': 0, 'class_name': 'person'},
            {'id': 1, 'bbox': [320, 100, 180, 160], 'confidence': 0.78, 'area': 28800, 'class': 56, 'class_name': 'chair'},
            {'id': 2, 'bbox': [100, 280, 190, 140], 'confidence': 0.92, 'area': 26600, 'class': 63, 'class_name': 'laptop'},
        ]
        
        return {
            'segments': segments,
            'count': len(segments),
            'success': True,
            'mock': True
        }

local_yolo = LocalYOLOModel()

