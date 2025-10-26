"""
Enhanced configuration for improved material detection accuracy
Uses custom-trained YOLO model for direct material classification
"""

import os
from typing import Dict, List, Tuple

class EnhancedConfig:
    # ============ ENHANCED DETECTION CONFIG ============

    # YOLO Model Configuration
    YOLO_CONFIDENCE_THRESHOLD = float(os.getenv('YOLO_CONFIDENCE_THRESHOLD', '0.10'))
    YOLO_IOU_THRESHOLD = float(os.getenv('YOLO_IOU_THRESHOLD', '0.45'))
    YOLO_MIN_AREA = int(os.getenv('YOLO_MIN_AREA', '300'))
    
    # Material Detection Configuration
    MATERIAL_CONFIDENCE_THRESHOLD = float(os.getenv('MATERIAL_CONFIDENCE_THRESHOLD', '0.15'))

    # ============ IMAGE ENHANCEMENT CONFIG ============

    # Image preprocessing
    ENHANCE_CONTRAST = float(os.getenv('ENHANCE_CONTRAST', '1.2'))  # 1.0 = no change
    ENHANCE_SHARPNESS = float(os.getenv('ENHANCE_SHARPNESS', '1.1'))
    ENHANCE_BRIGHTNESS = float(os.getenv('ENHANCE_BRIGHTNESS', '1.0'))

    # Target image size for YOLO (larger = better accuracy, slower)
    YOLO_INPUT_SIZE = int(os.getenv('YOLO_INPUT_SIZE', '640'))

    # ============ ACCURACY MONITORING CONFIG ============

    # Enable data collection for training
    COLLECT_TRAINING_DATA = os.getenv('COLLECT_TRAINING_DATA', 'false').lower() == 'true'
    TRAINING_DATA_DIR = os.getenv('TRAINING_DATA_DIR', 'training_data')

    # Accuracy monitoring
    ENABLE_ACCURACY_MONITORING = os.getenv('ENABLE_ACCURACY_MONITORING', 'true').lower() == 'true'

    # Auto-correction features
    USE_TEMPORAL_CONSISTENCY = os.getenv('USE_TEMPORAL_CONSISTENCY', 'true').lower() == 'true'
    TEMPORAL_WINDOW_SIZE = int(os.getenv('TEMPORAL_WINDOW_SIZE', '5'))  # frames

    # ============ MATERIAL TO DRUM MAPPING ============
    
    MATERIAL_TO_DRUM = {
        "wood": "kick",
        "metal": "cymbal",
        "plastic": "tom",
        "glass": "hihat",
        "ceramic": "tom",
        "fabric": "snare",
        "paper": "snare",
        "rubber": "tom",
        "stone": "kick",
        "brick": "kick",
        "carpet": "snare",
        "foliage": "snare",
        "food": "tom",
        "hair": "snare",
        "leather": "snare",
        "mirror": "hihat",
        "other": "snare",
        "painted": "tom",
        "polished_stone": "kick",
        "skin": "snare",
        "sky": "hihat",
        "tile": "kick",
        "wallpaper": "snare",
        "water": "hihat",
        "unknown": "snare"
    }

    # ============ PERFORMANCE OPTIMIZATION ============

    # Batch processing for multiple materials
    ENABLE_BATCH_PROCESSING = os.getenv('ENABLE_BATCH_PROCESSING', 'true').lower() == 'true'
    MAX_BATCH_SIZE = int(os.getenv('MAX_BATCH_SIZE', '8'))

    # Multi-threading for parallel processing
    USE_PARALLEL_PROCESSING = os.getenv('USE_PARALLEL_PROCESSING', 'false').lower() == 'true'
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '4'))

# Usage example in your app.py:
# from enhanced_config import EnhancedConfig
# enhanced_config = EnhancedConfig()