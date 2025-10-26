"""
Object-aware material classifier that considers object context
"""

import numpy as np
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
from typing import Dict, List, Optional, Tuple
import logging
import base64
import io

logger = logging.getLogger(__name__)

class ObjectAwareMaterialClassifier:
    def __init__(self):
        """Initialize CLIP model with object-aware material classification."""
        logger.info("Loading object-aware material classifier...")

        model_name = "openai/clip-vit-base-patch32"
        self.clip_model = CLIPModel.from_pretrained(model_name)
        self.clip_processor = CLIPProcessor.from_pretrained(model_name)

        # Object-specific material mappings based on common sense
        self.object_material_priors = {
            "couch": ["fabric", "leather", "velvet", "microfiber"],
            "chair": ["wood", "metal", "plastic", "fabric"],
            "cup": ["ceramic", "glass", "plastic", "metal"],
            "bowl": ["ceramic", "glass", "metal", "plastic"],
            "bottle": ["glass", "plastic"],
            "book": ["paper", "cardboard"],
            "laptop": ["metal", "plastic"],
            "phone": ["metal", "plastic", "glass"],
            "table": ["wood", "metal", "glass"],
            "person": ["fabric", "skin", "cotton"],  # clothing
            "cat": ["fur", "soft"],
            "dog": ["fur", "soft"],
            "car": ["metal", "plastic"],
            "tv": ["plastic", "metal", "glass"],
            "keyboard": ["plastic", "metal"],
            "mouse": ["plastic"],
            "remote": ["plastic"],
            "spoon": ["metal", "plastic"],
            "fork": ["metal", "plastic"],
            "knife": ["metal"],
            "plate": ["ceramic", "plastic", "glass"],
            "vase": ["ceramic", "glass"],
            "clock": ["plastic", "metal", "wood"]
        }

        # Fallback materials for unknown objects
        self.fallback_materials = [
            "wood", "metal", "plastic", "glass",
            "fabric", "paper", "ceramic", "rubber"
        ]

        # Enhanced confidence thresholds
        self.confidence_threshold = 0.35  # Higher threshold
        self.min_score_spread = 0.10      # Require more decisive classification

        # Device setup
        if torch.backends.mps.is_available():
            self.device = "mps"
            logger.info("Using MPS acceleration")
        elif torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"

        self.clip_model.to(self.device)
        self.clip_model.eval()

        logger.info("Object-aware material classifier ready")

    def classify_segment_material(self, image_crop: Image.Image, object_class: str, debug: bool = False) -> str:
        """Classify material considering the object context."""

        # Get object-specific materials to test
        candidate_materials = self.object_material_priors.get(object_class, self.fallback_materials)

        if debug:
            logger.info(f"  Classifying {object_class} with candidates: {candidate_materials}")

        # Create enhanced prompts for the specific object
        prompts = []
        for material in candidate_materials:
            # Object-aware prompts
            prompts.extend([
                f"a {material} {object_class}",
                f"{object_class} made of {material}",
                f"{material} surface of {object_class}"
            ])

        # Process prompts
        inputs = self.clip_processor(text=prompts, return_tensors="pt", padding=True).to(self.device)

        with torch.no_grad():
            text_features = self.clip_model.get_text_features(**inputs)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)

        # Process image
        inputs = self.clip_processor(images=image_crop, return_tensors="pt").to(self.device)

        with torch.no_grad():
            image_features = self.clip_model.get_image_features(**inputs)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

            # Compute similarities
            similarities = (image_features @ text_features.T).squeeze(0)

        # Average similarities for each material (3 prompts per material)
        material_scores = []
        for i in range(len(candidate_materials)):
            start_idx = i * 3
            end_idx = start_idx + 3
            avg_score = similarities[start_idx:end_idx].mean().item()
            material_scores.append(avg_score)

        # Get best material
        best_idx = np.argmax(material_scores)
        best_score = material_scores[best_idx]
        best_material = candidate_materials[best_idx]

        if debug:
            logger.info(f"  Object-aware material scores for {object_class}:")
            for i, (material, score) in enumerate(zip(candidate_materials, material_scores)):
                marker = " <- BEST" if i == best_idx else ""
                logger.info(f"    {material}: {score:.3f}{marker}")

        # Enhanced confidence checking
        score_spread = max(material_scores) - min(material_scores)

        if len(material_scores) > 1:
            second_best = sorted(material_scores, reverse=True)[1]
            margin = best_score - second_best
        else:
            margin = 0.1

        if debug:
            logger.info(f"  Score spread: {score_spread:.3f}, Margin: {margin:.3f}")

        # Confidence checks with object-aware logic
        if score_spread < self.min_score_spread:
            if debug:
                logger.info(f"  ⚠️  Low confidence: Using object-based fallback")
            return self._get_object_fallback_material(object_class)
        elif margin < 0.05:
            if debug:
                logger.info(f"  ⚠️  Ambiguous: Using object-based fallback")
            return self._get_object_fallback_material(object_class)
        elif best_score < self.confidence_threshold:
            if debug:
                logger.info(f"  ⚠️  Low score: Using object-based fallback")
            return self._get_object_fallback_material(object_class)

        return best_material

    def _get_object_fallback_material(self, object_class: str) -> str:
        """Get most likely material based on object type when classification fails."""
        # Common sense fallbacks
        object_fallbacks = {
            "couch": "fabric",
            "chair": "wood",
            "cup": "ceramic",
            "bowl": "ceramic",
            "bottle": "plastic",
            "book": "paper",
            "laptop": "metal",
            "phone": "plastic",
            "table": "wood",
            "person": "fabric",  # clothing
            "cat": "fabric",     # fur-like
            "dog": "fabric",     # fur-like
            "car": "metal",
            "tv": "plastic",
            "keyboard": "plastic",
            "mouse": "plastic",
            "remote": "plastic",
            "spoon": "metal",
            "fork": "metal",
            "knife": "metal",
            "plate": "ceramic",
            "vase": "ceramic",
            "clock": "plastic"
        }

        return object_fallbacks.get(object_class, "plastic")  # Default fallback

    def classify_segments(self, frame_data: str, segments: Dict[str, any]) -> Dict[int, str]:
        """Classify materials for all segments using object-aware approach."""
        logger.info("Starting object-aware material classification...")

        # Decode image
        if frame_data.startswith('data:'):
            frame_data = frame_data.split(',', 1)[1]
        img_bytes = base64.b64decode(frame_data)
        image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        image_np = np.array(image)

        segment_list = segments.get('segments', [])
        if not segment_list:
            logger.warning("No segments provided")
            return {}

        materials = {}
        logger.info(f"Object-aware classification of {len(segment_list)} segments...")

        for i, segment in enumerate(segment_list):
            segment_id = segment.get('id', i)
            bbox = segment.get('bbox', [])
            object_class = segment.get('class_name', 'unknown')

            if len(bbox) >= 4:
                # Extract crop
                x, y, w, h = bbox
                x1, y1 = int(x), int(y)
                x2, y2 = int(x + w), int(y + h)

                # Clip to bounds
                h_img, w_img = image_np.shape[:2]
                x1, x2 = max(0, x1), min(w_img, x2)
                y1, y2 = max(0, y1), min(h_img, y2)

                crop = image_np[y1:y2, x1:x2]
                if crop.size == 0:
                    crop = np.ones((64, 64, 3), dtype=np.uint8) * 255

                crop_img = Image.fromarray(crop)

                logger.info(f"  Segment {segment_id} ({object_class}):")
                material = self.classify_segment_material(crop_img, object_class, debug=True)
                materials[segment_id] = material
                logger.info(f"    -> Result: {material}")
            else:
                materials[segment_id] = self._get_object_fallback_material(segment.get('class_name', 'unknown'))

        logger.info("Object-aware material classification complete")
        return materials

# Global instance
object_aware_material_classifier = ObjectAwareMaterialClassifier()