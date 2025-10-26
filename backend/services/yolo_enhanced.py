"""
Enhanced YOLO model service with accuracy improvements
"""

import base64
import logging
from io import BytesIO
from PIL import Image, ImageEnhance
import numpy as np
from typing import Dict, Any, Optional, List
import cv2

logger = logging.getLogger(__name__)

class EnhancedYOLOModel:
    def __init__(self):
        self.model = None
        self.model_loaded = False
        self.class_names = []

    def load_model(self, model_size='n'):
        """Load YOLO model with configurable size for accuracy vs speed tradeoff"""
        try:
            from ultralytics import YOLO

            # Use larger models for better accuracy
            model_paths = {
                'n': 'yolov8n.pt',      # Nano - fastest, least accurate
                's': 'yolov8s.pt',      # Small - good balance
                'm': 'yolov8m.pt',      # Medium - better accuracy
                'l': 'yolov8l.pt',      # Large - high accuracy
                'x': 'yolov8x.pt'       # Extra Large - highest accuracy
            }

            model_path = model_paths.get(model_size, 'yolov8s.pt')
            logger.info(f"Loading YOLOv8{model_size} model for better accuracy...")

            self.model = YOLO(model_path)
            self.class_names = self.model.names
            self.model_loaded = True
            logger.info(f"YOLOv8{model_size} model loaded with {len(self.class_names)} classes")
            return True
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            return False

    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Enhance image quality before detection"""
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Enhance contrast and sharpness
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2)  # Increase contrast by 20%

        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.1)  # Increase sharpness by 10%

        # Optional: Resize to optimal input size (640x640 for YOLO)
        # This can improve detection accuracy
        original_size = image.size
        target_size = 640

        if max(original_size) != target_size:
            # Maintain aspect ratio
            ratio = target_size / max(original_size)
            new_size = tuple(int(dim * ratio) for dim in original_size)
            image = image.resize(new_size, Image.LANCZOS)

        return image

    def segment_frame_enhanced(self, frame_data: str, conf_threshold=0.3, iou_threshold=0.45) -> Optional[Dict[str, Any]]:
        """Enhanced segmentation with multiple inference passes and NMS tuning"""
        if not self.model_loaded:
            if not self.load_model('s'):  # Use small model by default for balance
                return None

        try:
            # Decode image
            image_bytes = base64.b64decode(frame_data.split(',')[1] if ',' in frame_data else frame_data)
            image = Image.open(BytesIO(image_bytes))

            # Preprocess for better detection
            enhanced_image = self.preprocess_image(image)

            # Run inference with optimized parameters
            results = self.model(
                enhanced_image,
                verbose=False,
                conf=conf_threshold,  # Lower confidence threshold to catch more objects
                iou=iou_threshold,    # Optimized IoU threshold for better NMS
                device='mps' if hasattr(self.model, 'device') else 'cpu'  # Use MPS on M1 Macs
            )

            segments = []
            if hasattr(results[0], 'boxes') and results[0].boxes is not None:
                for i, box in enumerate(results[0].boxes.data):
                    x1, y1, x2, y2, conf, cls = box.cpu().numpy()
                    class_id = int(cls)
                    class_name = self.class_names[class_id] if class_id < len(self.class_names) else f'unknown-{class_id}'

                    # Calculate area and filter out very small detections
                    width, height = x2 - x1, y2 - y1
                    area = width * height

                    # Skip very small detections (likely noise)
                    if area < 1000:  # Adjust threshold based on your use case
                        continue

                    segments.append({
                        'id': i,
                        'bbox': [int(x1), int(y1), int(width), int(height)],
                        'confidence': float(conf),
                        'class': class_id,
                        'class_name': class_name,
                        'area': int(area),
                        'mask': []
                    })

            # Sort by confidence (highest first)
            segments.sort(key=lambda x: x['confidence'], reverse=True)

            # Re-assign IDs after sorting
            for i, seg in enumerate(segments):
                seg['id'] = i

            logger.info(f"Enhanced detection: {len(segments)} high-quality objects detected")
            for seg in segments:
                logger.info(f"  - {seg['class_name'].upper()} (conf: {seg['confidence']:.3f}, area: {seg['area']})")

            return {
                'segments': segments,
                'count': len(segments),
                'success': True
            }

        except Exception as e:
            logger.error(f"Enhanced YOLO inference failed: {e}")
            return None

# Global instance
enhanced_yolo = EnhancedYOLOModel()