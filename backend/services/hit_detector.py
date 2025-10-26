"""
Hit Detector Service
Extracts impact data from ESP32 sensor messages
"""

import time
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class ImpactEvent:

    velocity: float
    magnitude: float
    timestamp: int
    id: int
    position: Optional[Tuple[int, int]] = None
    material: Optional[str] = None


class HitDetector:

    def process_sensor_data(self, data: dict) -> Optional[ImpactEvent]:

        impact = ImpactEvent(
            velocity=data.get("velocity", 0),
            magnitude=data["magnitude"],
            timestamp=data["timestamp"],
            id=data["id"]
        )

        # Note: technically magnitude is just 0.1 * velocity,
        # but keeping because it (or something similar) might be useful later

        return impact