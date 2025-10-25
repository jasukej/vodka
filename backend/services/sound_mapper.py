from typing import Optional
from services.hit_detector import HitDetector, ImpactEvent
from services.cv_localizer import CVLocalizer
from services.audio_player import AudioPlayer


class SoundMapper:

    def __init__(self):
        self.hit_detector = HitDetector()
        self.cv_localizer = CVLocalizer()
        self.audio_player = AudioPlayer()
        print("SoundMapper: Initialized all services")

    async def process_impact(self, impact_data: dict) -> Optional[dict]:
        # Step 1: Validate and process sensor data
        impact = self.hit_detector.process_sensor_data(impact_data)

        if impact is None:
            return None

        # Step 2: Determine impact coordinates
        x, y = self.cv_localizer.get_coordinate_from_impact(impact_data)
        impact.position = (x, y)

        # Step 3: Map coordinates to material
        impact.material = self.cv_localizer.get_material_from_coordinate(x, y)

        # Step 4: Play sound
        self.audio_player.play_sound(impact.material, impact.velocity)

        print(f"Impact: {impact.material} at ({x}, {y}), velocity={impact.velocity:.2f}")

        # Return impact info for client acknowledgment
        return {
            "material": impact.material,
            "position": impact.position,
            "velocity": impact.velocity,
            "timestamp": impact.timestamp
        }

    def cleanup(self):
        self.cv_localizer.cleanup()
        self.audio_player.cleanup()
        print("SoundMapper: Cleaned up all services")
