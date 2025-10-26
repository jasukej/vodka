"""
Enhanced configuration for improved accuracy
Add these settings to your config.py or create a new enhanced_config.py
"""

import os
from typing import Dict, List, Tuple

class EnhancedConfig:
    # ============ ENHANCED DETECTION CONFIG ============

    # YOLO Model Configuration
    YOLO_MODEL_SIZE = os.getenv('YOLO_MODEL_SIZE', 's')  # n, s, m, l, x (s is good balance)
    YOLO_CONFIDENCE_THRESHOLD = float(os.getenv('YOLO_CONFIDENCE_THRESHOLD', '0.3'))  # Lower = more objects
    YOLO_IOU_THRESHOLD = float(os.getenv('YOLO_IOU_THRESHOLD', '0.45'))  # Non-max suppression
    YOLO_MIN_AREA = int(os.getenv('YOLO_MIN_AREA', '1000'))  # Minimum object area in pixels

    # Material Classification Configuration
    CLIP_MODEL_SIZE = os.getenv('CLIP_MODEL_SIZE', 'large')  # base, large (large = better accuracy)
    MATERIAL_CONFIDENCE_THRESHOLD = float(os.getenv('MATERIAL_CONFIDENCE_THRESHOLD', '0.25'))
    MATERIAL_MIN_SCORE_SPREAD = float(os.getenv('MATERIAL_MIN_SCORE_SPREAD', '0.08'))
    USE_ENSEMBLE_CLASSIFICATION = os.getenv('USE_ENSEMBLE_CLASSIFICATION', 'true').lower() == 'true'

    # Enhanced Material Categories
    ENHANCED_MATERIALS = [
        "smooth wood",
        "rough wood",
        "metal steel",
        "metal aluminum",
        "hard plastic",
        "soft plastic",
        "clear glass",
        "ceramic",
        "fabric textile",
        "paper cardboard",
        "rubber material",
        "stone concrete"
    ]

    # Material Simplification Mapping
    MATERIAL_MAPPING = {
        "smooth wood": "wood",
        "rough wood": "wood",
        "metal steel": "metal",
        "metal aluminum": "metal",
        "hard plastic": "plastic",
        "soft plastic": "plastic",
        "clear glass": "glass",
        "fabric textile": "fabric",
        "paper cardboard": "paper",
        "rubber material": "rubber",
        "stone concrete": "stone"
    }

    # ============ IMAGE ENHANCEMENT CONFIG ============

    # Image preprocessing
    ENHANCE_CONTRAST = float(os.getenv('ENHANCE_CONTRAST', '1.2'))  # 1.0 = no change
    ENHANCE_SHARPNESS = float(os.getenv('ENHANCE_SHARPNESS', '1.1'))
    ENHANCE_BRIGHTNESS = float(os.getenv('ENHANCE_BRIGHTNESS', '1.0'))

    # Target image size for YOLO (larger = better accuracy, slower)
    YOLO_INPUT_SIZE = int(os.getenv('YOLO_INPUT_SIZE', '640'))  # 640, 1280

    # Minimum crop size for material classification
    MIN_CROP_SIZE = int(os.getenv('MIN_CROP_SIZE', '100'))
    TARGET_CROP_SIZE = int(os.getenv('TARGET_CROP_SIZE', '224'))  # CLIP optimal size

    # ============ ACCURACY MONITORING CONFIG ============

    # Enable data collection for training
    COLLECT_TRAINING_DATA = os.getenv('COLLECT_TRAINING_DATA', 'false').lower() == 'true'
    TRAINING_DATA_DIR = os.getenv('TRAINING_DATA_DIR', 'training_data')

    # Accuracy monitoring
    ENABLE_ACCURACY_MONITORING = os.getenv('ENABLE_ACCURACY_MONITORING', 'true').lower() == 'true'

    # Auto-correction features
    USE_TEMPORAL_CONSISTENCY = os.getenv('USE_TEMPORAL_CONSISTENCY', 'true').lower() == 'true'
    TEMPORAL_WINDOW_SIZE = int(os.getenv('TEMPORAL_WINDOW_SIZE', '5'))  # frames

    # ============ DRUM MAPPING IMPROVEMENTS ============

    # Enhanced sound mapping based on object class + material
    ENHANCED_SOUND_MAPPING = {
        # Object-Material combinations for more accurate sound selection
        ("bottle", "glass"): "hat",
        ("bottle", "plastic"): "snare",
        ("cup", "ceramic"): "tom",
        ("cup", "metal"): "cymbal",
        ("book", "paper"): "snare",
        ("laptop", "metal"): "kick",
        ("chair", "wood"): "bass",
        ("chair", "metal"): "hihat",
        ("bowl", "ceramic"): "bell",
        ("bowl", "metal"): "crash",
        # Default material mappings
        ("unknown", "wood"): "bass",
        ("unknown", "metal"): "hihat",
        ("unknown", "plastic"): "snare",
        ("unknown", "glass"): "hat",
        ("unknown", "ceramic"): "tom",
        ("unknown", "fabric"): "snare",
        ("unknown", "paper"): "snare",
        ("unknown", "rubber"): "kick"
    }

    # Fallback to simple material mapping if object class unknown
    MATERIAL_TO_DRUM = {
        "wood": "bass",
        "metal": "hihat",
        "plastic": "snare",
        "glass": "hat",
        "ceramic": "tom",
        "fabric": "snare",
        "paper": "snare",
        "rubber": "kick",
        "stone": "kick",
        "unknown": "snare"
    }

    # ============ PERFORMANCE OPTIMIZATION ============

    # Batch processing for multiple segments
    ENABLE_BATCH_PROCESSING = os.getenv('ENABLE_BATCH_PROCESSING', 'true').lower() == 'true'
    MAX_BATCH_SIZE = int(os.getenv('MAX_BATCH_SIZE', '8'))

    # Cache embeddings
    CACHE_EMBEDDINGS = os.getenv('CACHE_EMBEDDINGS', 'true').lower() == 'true'

    # Multi-threading for parallel processing
    USE_PARALLEL_PROCESSING = os.getenv('USE_PARALLEL_PROCESSING', 'false').lower() == 'true'
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '4'))

# Usage example in your app.py:
# from enhanced_config import EnhancedConfig
# enhanced_config = EnhancedConfig()