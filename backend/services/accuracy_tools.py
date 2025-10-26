"""
Data collection and validation tools for improving classification accuracy
"""

import os
import json
import time
import logging
from typing import Dict, List, Tuple
from PIL import Image
import base64
import io

logger = logging.getLogger(__name__)

class DataCollectionTool:
    def __init__(self, save_dir: str = "training_data"):
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        os.makedirs(f"{save_dir}/images", exist_ok=True)
        os.makedirs(f"{save_dir}/annotations", exist_ok=True)

    def collect_calibration_sample(self, frame_data: str, segments: Dict, materials: Dict,
                                 user_corrections: Dict = None) -> str:
        """Collect a labeled sample from calibration for improving accuracy."""
        timestamp = int(time.time())
        sample_id = f"sample_{timestamp}"

        # Save image
        image = self._decode_image(frame_data)
        image_path = f"{self.save_dir}/images/{sample_id}.jpg"
        image.save(image_path)

        # Save annotations
        annotation = {
            "sample_id": sample_id,
            "timestamp": timestamp,
            "segments": segments.get('segments', []),
            "predicted_materials": materials,
            "user_corrections": user_corrections or {},
            "image_path": image_path
        }

        annotation_path = f"{self.save_dir}/annotations/{sample_id}.json"
        with open(annotation_path, 'w') as f:
            json.dump(annotation, f, indent=2)

        logger.info(f"Collected training sample: {sample_id}")
        return sample_id

    def validate_predictions(self, true_materials: Dict[int, str],
                           predicted_materials: Dict[int, str]) -> Dict:
        """Calculate accuracy metrics for material predictions."""
        if not true_materials or not predicted_materials:
            return {"accuracy": 0.0, "matches": 0, "total": 0}

        matches = 0
        total = 0
        errors = []

        for seg_id in true_materials:
            if seg_id in predicted_materials:
                total += 1
                if true_materials[seg_id] == predicted_materials[seg_id]:
                    matches += 1
                else:
                    errors.append({
                        "segment_id": seg_id,
                        "true": true_materials[seg_id],
                        "predicted": predicted_materials[seg_id]
                    })

        accuracy = matches / total if total > 0 else 0.0

        return {
            "accuracy": accuracy,
            "matches": matches,
            "total": total,
            "errors": errors
        }

    def _decode_image(self, frame_data: str) -> Image.Image:
        """Decode base64 data URI to PIL Image."""
        if frame_data.startswith('data:'):
            frame_data = frame_data.split(',', 1)[1]
        img_bytes = base64.b64decode(frame_data)
        return Image.open(io.BytesIO(img_bytes)).convert("RGB")

class AccuracyMonitor:
    def __init__(self):
        self.predictions = []
        self.ground_truth = []

    def add_prediction(self, segment_id: int, predicted: str, actual: str = None):
        """Add a prediction for accuracy tracking."""
        self.predictions.append({
            "segment_id": segment_id,
            "predicted": predicted,
            "actual": actual,
            "timestamp": time.time()
        })

    def calculate_metrics(self) -> Dict:
        """Calculate accuracy metrics over all predictions."""
        if not self.predictions:
            return {"accuracy": 0.0, "total": 0}

        # Filter predictions with ground truth
        valid_predictions = [p for p in self.predictions if p.get('actual')]

        if not valid_predictions:
            return {"accuracy": 0.0, "total": len(self.predictions), "validated": 0}

        correct = sum(1 for p in valid_predictions if p['predicted'] == p['actual'])
        total = len(valid_predictions)

        # Material-wise accuracy
        material_stats = {}
        for p in valid_predictions:
            actual = p['actual']
            if actual not in material_stats:
                material_stats[actual] = {"correct": 0, "total": 0}
            material_stats[actual]["total"] += 1
            if p['predicted'] == actual:
                material_stats[actual]["correct"] += 1

        for material in material_stats:
            stats = material_stats[material]
            stats["accuracy"] = stats["correct"] / stats["total"]

        return {
            "overall_accuracy": correct / total,
            "total_predictions": len(self.predictions),
            "validated_predictions": total,
            "material_accuracy": material_stats
        }

# Global instances
data_collector = DataCollectionTool()
accuracy_monitor = AccuracyMonitor()