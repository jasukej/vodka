"""
M1-optimized Material Classifier
Integrates with existing YOLO segmentation, uses CLIP for material classification.
Optimized for Apple Silicon with MPS acceleration.
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

class MaterialClassifier:
    def __init__(self):
        """Initialize CLIP model optimized for M1."""
        logger.info("Loading CLIP model for material classification...")

        # Use lightweight CLIP model
        model_name = "openai/clip-vit-base-patch32"
        self.clip_model = CLIPModel.from_pretrained(model_name)
        self.clip_processor = CLIPProcessor.from_pretrained(model_name)

        # Real-world material types (not drum-specific)
        # These classify what the actual surface is made of (like Minecraft blocks)
        # The sound mapper will then map these materials to drum sounds
        self.material_types = [
            "wood",
            "metal",
            "plastic",
            "glass",
            "fabric",
            "paper",
            "ceramic",
            "rubber"
        ]

        # Confidence threshold - if max similarity is below this, return "unknown"
        self.confidence_threshold = 0.27

        # Minimum score spread - if the difference between best and worst is too low,
        # the model is essentially guessing and we should return "unknown"
        self.min_score_spread = 0.05

        # Detect device (MPS for M1/M2/M3, else CPU)
        if torch.backends.mps.is_available():
            self.device = "mps"
            logger.info("Using MPS (Metal Performance Shaders) acceleration")
        elif torch.cuda.is_available():
            self.device = "cuda"
            logger.info("Using CUDA acceleration")
        else:
            self.device = "cpu"
            logger.info("Using CPU (consider using M1/M2 Mac for MPS acceleration)")

        self.clip_model.to(self.device)
        self.clip_model.eval()  # Set to evaluation mode

        # Pre-compute text embeddings for materials (do once for speed)
        logger.info("Pre-computing material embeddings...")
        self.material_embeddings = self._precompute_material_embeddings()

        # Storage for processed results
        self.segment_map = None  # 2D array mapping pixels to segment IDs
        self.segment_materials = {}  # segment_id -> material_type

        logger.info(f"Material classifier ready on {self.device}")

    def _precompute_material_embeddings(self) -> torch.Tensor:
        """Pre-compute CLIP embeddings for all material types."""
        # Try multiple prompt variations and average them for better accuracy
        prompt_templates = [
            "a photo of {}",
            "a {} object",
            "made of {}",
            "{} material"
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
        # Re-normalize after averaging
        avg_embeddings = avg_embeddings / avg_embeddings.norm(dim=-1, keepdim=True)

        logger.info(f"Pre-computed embeddings using {len(prompt_templates)} prompt templates")
        return avg_embeddings

    def classify_segments(
        self,
        frame_data: str,
        segments: Dict[str, any]
    ) -> Dict[int, str]:
        """
        Classify materials for all segments using existing YOLO segmentation.

        Args:
            frame_data: Base64 encoded image data URI
            segments: Segmentation results from model_service

        Returns:
            Dictionary mapping segment_id -> material_name
        """
        logger.info("Starting material classification...")

        # Warn if image quality might be poor
        logger.info("NOTE: Material classification works best with:")
        logger.info("  - Real camera images (not mock/synthetic data)")
        logger.info("  - Simple single-material objects (wooden spoon, metal can, plastic bottle)")
        logger.info("  - Clear, well-lit close-ups showing texture")
        logger.info("  - Objects that are NOT complex multi-material items (TVs, beds, people)")

        start_time = torch.cuda.Event(enable_timing=True) if self.device == "cuda" else None
        end_time = torch.cuda.Event(enable_timing=True) if self.device == "cuda" else None

        if start_time:
            start_time.record()

        # Decode base64 image
        image = self._decode_image(frame_data)
        image_np = np.array(image)

        segment_list = segments.get('segments', [])
        if not segment_list:
            logger.warning("No segments provided for material classification")
            return {}

        # Create pixel-to-segment map for instant lookups
        self.segment_map = self._create_segment_map(segment_list, image_np.shape[:2])

        # Classify each segment
        materials = {}
        logger.info(f"Classifying {len(segment_list)} segments...")

        for i, segment in enumerate(segment_list):
            segment_id = segment.get('id', i)
            bbox = segment.get('bbox', [])

            if len(bbox) >= 4:
                # Extract segment region
                segment_crop = self._extract_segment_crop(image_np, bbox)

                # Classify material with debug logging enabled
                class_name = segment.get('class_name', 'unknown')
                logger.info(f"  Segment {segment_id} ({class_name}):")
                logger.info(f"    Crop size: {segment_crop.size}")
                logger.info(f"    BBox: {bbox}")
                material = self._classify_material_fast(segment_crop, debug=True)
                materials[segment_id] = material

                logger.info(f"    -> Result: {material}")
            else:
                materials[segment_id] = "unknown"

        self.segment_materials = materials

        if start_time:
            end_time.record()
            torch.cuda.synchronize()
            elapsed = start_time.elapsed_time(end_time) / 1000.0
            logger.info(f"Material classification complete in {elapsed:.2f}s")
        else:
            logger.info("Material classification complete")

        return materials

    def _decode_image(self, frame_data: str) -> Image.Image:
        """Decode base64 data URI to PIL Image."""
        # Handle data URI format: "data:image/jpeg;base64,..."
        if frame_data.startswith('data:'):
            frame_data = frame_data.split(',', 1)[1]

        img_bytes = base64.b64decode(frame_data)
        return Image.open(io.BytesIO(img_bytes)).convert("RGB")

    def _create_segment_map(self, segments: List[Dict], shape: Tuple[int, int]) -> np.ndarray:
        """Create a 2D map where each pixel maps to a segment ID for O(1) lookups."""
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
        """Extract the segment region from the image."""
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

        return Image.fromarray(crop)

    def _classify_material_fast(self, image: Image.Image, debug: bool = False) -> str:
        """Classify material using pre-computed embeddings for speed."""
        # Process image
        inputs = self.clip_processor(images=image, return_tensors="pt").to(self.device)

        with torch.no_grad():
            # Get image features
            image_features = self.clip_model.get_image_features(**inputs)
            # Normalize
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)

            # Compute similarity with pre-computed material embeddings
            similarity = (image_features @ self.material_embeddings.T).squeeze(0)

            # Get best match
            best_idx = similarity.argmax().item()
            best_score = similarity[best_idx].item()

            # Debug logging - show all scores (always enabled for now)
            logger.info("  Material classification scores:")
            scores = similarity.tolist()
            sorted_scores = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
            for idx, score in sorted_scores:
                mat_type = self.material_types[idx]
                marker = " <- BEST" if idx == best_idx else ""
                logger.info(f"    {mat_type}: {score:.3f}{marker}")

            # Show score spread to diagnose confidence issues
            score_spread = max(scores) - min(scores)
            logger.info(f"  Score spread: {score_spread:.3f} (higher = more confident)")

            # Return the best match material
            material = self.material_types[best_idx]

            # Show warnings if confidence is low, but still return the best guess
            if score_spread < self.min_score_spread:
                logger.info(f"  ⚠️  Low confidence: score spread {score_spread:.3f} < {self.min_score_spread}")
                logger.info(f"  Returning best guess: {material}")
            elif best_score < self.confidence_threshold:
                logger.info(f"  ⚠️  Low confidence: best score {best_score:.3f} < {self.confidence_threshold}")
                logger.info(f"  Returning best guess: {material}")

        return material

    def query(self, x: int, y: int) -> Optional[str]:
        """
        Query the material at a specific pixel coordinate.
        O(1) lookup after classification.

        Args:
            x: X coordinate (pixels)
            y: Y coordinate (pixels)

        Returns:
            Material type string or None if out of bounds
        """
        if self.segment_map is None:
            logger.warning("Must call classify_segments() first")
            return None

        # Check bounds
        if (y < 0 or y >= self.segment_map.shape[0] or
            x < 0 or x >= self.segment_map.shape[1]):
            return None

        # Lookup segment
        seg_id = self.segment_map[y, x]
        if seg_id == -1:
            return None

        # Return material
        return self.segment_materials.get(seg_id, "unknown")

    def get_segment_material(self, segment_id: int) -> Optional[str]:
        """Get material for a specific segment ID."""
        return self.segment_materials.get(segment_id)

    def get_all_materials(self) -> Dict[int, str]:
        """Get all segment materials."""
        return self.segment_materials.copy()

# Global instance
material_classifier = MaterialClassifier()
