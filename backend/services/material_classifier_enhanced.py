"""
Enhanced Material Classifier with improved accuracy techniques
"""

import numpy as np
from PIL import Image, ImageFilter, ImageEnhance
import torch
from transformers import CLIPProcessor, CLIPModel
from typing import Dict, List, Optional, Tuple
import logging
import base64
import io
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class EnhancedMaterialClassifier:
    def __init__(self):
        """Initialize enhanced CLIP model with accuracy improvements."""
        logger.info("Loading enhanced CLIP model for material classification...")

        # Use more powerful CLIP model for better accuracy
        model_name = "openai/clip-vit-large-patch14"  # Larger model for better accuracy
        self.clip_model = CLIPModel.from_pretrained(model_name)
        self.clip_processor = CLIPProcessor.from_pretrained(model_name)

        # Enhanced material types with more specific categories
        self.material_types = [
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

        # Adjusted thresholds for better accuracy
        self.confidence_threshold = 0.25  # Lower threshold
        self.min_score_spread = 0.08      # Higher spread requirement

        # Detect device
        if torch.backends.mps.is_available():
            self.device = "mps"
            logger.info("Using MPS (Metal Performance Shaders) acceleration")
        elif torch.cuda.is_available():
            self.device = "cuda"
            logger.info("Using CUDA acceleration")
        else:
            self.device = "cpu"
            logger.info("Using CPU")

        self.clip_model.to(self.device)
        self.clip_model.eval()

        # Enhanced prompt engineering
        logger.info("Pre-computing enhanced material embeddings...")
        self.material_embeddings = self._precompute_enhanced_embeddings()

        # Storage
        self.segment_map = None
        self.segment_materials = {}

        logger.info(f"Enhanced material classifier ready on {self.device}")

    def _precompute_enhanced_embeddings(self) -> torch.Tensor:
        """Pre-compute CLIP embeddings with enhanced prompt engineering."""
        # Multiple prompt templates for better accuracy
        prompt_templates = [
            "a photo of {}",
            "made of {}",
            "{} surface",
            "{} material texture",
            "close up view of {}",
            "{} object surface",
            "texture of {}"
        ]

        all_embeddings = []
        for template in prompt_templates:
            texts = [template.format(mat) for mat in self.material_types]
            inputs = self.clip_processor(text=texts, return_tensors="pt", padding=True).to(self.device)

            with torch.no_grad():
                text_features = self.clip_model.get_text_features(**inputs)
                text_features = text_features / text_features.norm(dim=-1, keepdim=True)
                all_embeddings.append(text_features)

        # Average all prompt embeddings
        avg_embeddings = torch.stack(all_embeddings).mean(dim=0)
        avg_embeddings = avg_embeddings / avg_embeddings.norm(dim=-1, keepdim=True)

        logger.info(f"Enhanced embeddings computed using {len(prompt_templates)} prompt templates")
        return avg_embeddings

    def _enhance_image_crop(self, image: Image.Image) -> List[Image.Image]:
        """Create multiple enhanced versions of the image crop for ensemble prediction."""
        enhanced_images = []

        # Original image
        enhanced_images.append(image)

        # Enhanced contrast
        enhancer = ImageEnhance.Contrast(image)
        enhanced_images.append(enhancer.enhance(1.3))

        # Enhanced sharpness
        enhancer = ImageEnhance.Sharpness(image)
        enhanced_images.append(enhancer.enhance(1.2))

        # Brightness adjustment
        enhancer = ImageEnhance.Brightness(image)
        enhanced_images.append(enhancer.enhance(1.1))

        # Slight blur to reduce noise
        enhanced_images.append(image.filter(ImageFilter.GaussianBlur(radius=0.5)))

        return enhanced_images

    def _classify_material_ensemble(self, image: Image.Image, debug: bool = False) -> str:
        """Classify material using ensemble of enhanced images."""
        # Create enhanced versions
        enhanced_images = self._enhance_image_crop(image)

        all_similarities = []

        for img in enhanced_images:
            # Process image
            inputs = self.clip_processor(images=img, return_tensors="pt").to(self.device)

            with torch.no_grad():
                # Get image features
                image_features = self.clip_model.get_image_features(**inputs)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)

                # Compute similarity with pre-computed material embeddings
                similarity = (image_features @ self.material_embeddings.T).squeeze(0)
                all_similarities.append(similarity.cpu().numpy())

        # Ensemble by averaging similarities
        avg_similarity = np.mean(all_similarities, axis=0)

        # Get best match
        best_idx = np.argmax(avg_similarity)
        best_score = avg_similarity[best_idx]

        # Calculate confidence metrics
        score_spread = np.max(avg_similarity) - np.min(avg_similarity)
        second_best_score = np.partition(avg_similarity, -2)[-2]
        margin = best_score - second_best_score

        if debug:
            logger.info("  Enhanced material classification scores:")
            sorted_indices = np.argsort(avg_similarity)[::-1]
            for i, idx in enumerate(sorted_indices):
                mat_type = self.material_types[idx]
                score = avg_similarity[idx]
                marker = " <- BEST" if idx == best_idx else ""
                logger.info(f"    {mat_type}: {score:.3f}{marker}")

            logger.info(f"  Score spread: {score_spread:.3f}")
            logger.info(f"  Margin to 2nd: {margin:.3f}")

        # Enhanced confidence checking
        material = self.material_types[best_idx]

        if score_spread < self.min_score_spread:
            logger.info(f"  ⚠️  Low confidence: score spread {score_spread:.3f} < {self.min_score_spread}")
            if score_spread < 0.05:  # Very low confidence
                material = "unknown"
                logger.info(f"  Returning: unknown (very low confidence)")
            else:
                logger.info(f"  Returning best guess: {material}")
        elif margin < 0.02:  # Very close scores
            logger.info(f"  ⚠️  Ambiguous: margin {margin:.3f} too small")
            logger.info(f"  Returning best guess: {material}")
        elif best_score < self.confidence_threshold:
            logger.info(f"  ⚠️  Low confidence: best score {best_score:.3f} < {self.confidence_threshold}")
            logger.info(f"  Returning best guess: {material}")

        # Simplify material names for drum mapping
        simplified_material = self._simplify_material_name(material)
        return simplified_material

    def _simplify_material_name(self, material: str) -> str:
        """Simplify enhanced material names to basic categories."""
        if "wood" in material:
            return "wood"
        elif "metal" in material:
            return "metal"
        elif "plastic" in material:
            return "plastic"
        elif "glass" in material:
            return "glass"
        elif "fabric" in material or "textile" in material:
            return "fabric"
        elif "paper" in material or "cardboard" in material:
            return "paper"
        elif "ceramic" in material:
            return "ceramic"
        elif "rubber" in material:
            return "rubber"
        elif "stone" in material or "concrete" in material:
            return "stone"
        else:
            return material

    def classify_segments_enhanced(
        self,
        frame_data: str,
        segments: Dict[str, any]
    ) -> Dict[int, str]:
        """Enhanced material classification with ensemble prediction."""
        logger.info("Starting enhanced material classification...")

        # Decode base64 image
        image = self._decode_image(frame_data)
        image_np = np.array(image)

        segment_list = segments.get('segments', [])
        if not segment_list:
            logger.warning("No segments provided for material classification")
            return {}

        # Create pixel-to-segment map
        self.segment_map = self._create_segment_map(segment_list, image_np.shape[:2])

        # Classify each segment with enhanced method
        materials = {}
        logger.info(f"Enhanced classification of {len(segment_list)} segments...")

        for i, segment in enumerate(segment_list):
            segment_id = segment.get('id', i)
            bbox = segment.get('bbox', [])

            if len(bbox) >= 4:
                # Extract segment region
                segment_crop = self._extract_segment_crop(image_np, bbox)

                # Enhanced classification with ensemble
                class_name = segment.get('class_name', 'unknown')
                logger.info(f"  Segment {segment_id} ({class_name}):")
                logger.info(f"    Crop size: {segment_crop.size}")
                logger.info(f"    BBox: {bbox}")

                material = self._classify_material_ensemble(segment_crop, debug=True)
                materials[segment_id] = material

                logger.info(f"    -> Enhanced result: {material}")
            else:
                materials[segment_id] = "unknown"

        self.segment_materials = materials
        logger.info("Enhanced material classification complete")
        return materials

    def _decode_image(self, frame_data: str) -> Image.Image:
        """Decode base64 data URI to PIL Image."""
        if frame_data.startswith('data:'):
            frame_data = frame_data.split(',', 1)[1]

        img_bytes = base64.b64decode(frame_data)
        return Image.open(io.BytesIO(img_bytes)).convert("RGB")

    def _create_segment_map(self, segments: List[Dict], shape: Tuple[int, int]) -> np.ndarray:
        """Create a 2D map where each pixel maps to a segment ID."""
        segment_map = np.full(shape, -1, dtype=np.int32)

        for segment in segments:
            segment_id = segment.get('id', 0)
            bbox = segment.get('bbox', [])

            if len(bbox) >= 4:
                x, y, w, h = bbox
                x1, y1 = int(x), int(y)
                x2, y2 = int(x + w), int(y + h)

                # Clip to image bounds
                x1, x2 = max(0, x1), min(shape[1], x2)
                y1, y2 = max(0, y1), min(shape[0], y2)

                segment_map[y1:y2, x1:x2] = segment_id

        return segment_map

    def _extract_segment_crop(self, image: np.ndarray, bbox: List[float]) -> Image.Image:
        """Extract and enhance the segment region."""
        x, y, w, h = bbox
        x1, y1 = int(x), int(y)
        x2, y2 = int(x + w), int(y + h)

        # Clip to image bounds
        h_img, w_img = image.shape[:2]
        x1, x2 = max(0, x1), min(w_img, x2)
        y1, y2 = max(0, y1), min(h_img, y2)

        crop = image[y1:y2, x1:x2]

        # Handle empty crops
        if crop.size == 0:
            crop = np.ones((64, 64, 3), dtype=np.uint8) * 255

        # Resize small crops for better CLIP processing
        crop_img = Image.fromarray(crop)
        if min(crop_img.size) < 100:  # Resize very small crops
            crop_img = crop_img.resize((224, 224), Image.LANCZOS)

        return crop_img

# Global instance
enhanced_material_classifier = EnhancedMaterialClassifier()