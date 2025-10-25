import cv2
import numpy as np
import time
import random
from typing import Optional, Tuple
from config import Config


class CVLocalizer:
    def __init__(self):
        self.camera = None
        self.material_map = None
        self._initialize_camera()

    def _initialize_camera(self):
        if Config.MOCK_CAMERA:
            print("CVLocalizer: MOCK MODE - using generated frames")
            self.camera = None
            return
        try:
            self.camera = cv2.VideoCapture(Config.CAMERA_INDEX)
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, Config.CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, Config.CAMERA_HEIGHT)
            self.camera.set(cv2.CAP_PROP_FPS, Config.CAMERA_FPS)
            print(f"CVLocalizer: Camera initialized on index {Config.CAMERA_INDEX}")
        except Exception as e:
            print(f"CVLocalizer: Failed to initialize camera: {e}")
            self.camera = None

    def classify_materials_once(self):
        # TODO: Implement material classification
        # material_regions = self.ml_model.detect_regions(self.latest_frame)
        # Config.MATERIAL_REGIONS = material_regions
        pass

    def get_stick_position(self) -> Optional[Tuple[int, int]]:
        if Config.MOCK_DETECTION:
            return self._generate_random_coordinate()

        # TODO: Real implementation - ArUco tracker manages its own frame capture
        #   return self.aruco_tracker.get_current_position()

        return None

    def get_material_from_coordinate(self, x: int, y: int) -> str:
        # TODO: May need to update if not using bounding boxes
        # Also MATERIAL_REGIONS may not be defined in Config
        for x_min, y_min, x_max, y_max, material in Config.MATERIAL_REGIONS:
            if x_min <= x < x_max and y_min <= y < y_max:
                return material

        return "default"

    def get_coordinate_from_impact(self, impact_data: dict) -> Tuple[int, int]:
        if Config.MOCK_COORDINATES:
            x, y = self._generate_random_coordinate()
            print(f"Generated random coordinates: ({x}, {y})")
            return (x, y)

        # Real detection - tracker handles frame capture internally
        x, y = self.get_stick_position()
        print(f"Detected stick position: ({x}, {y})")
        return (x, y)

    def cleanup(self):
        if self.camera is not None:
            self.camera.release()
        cv2.destroyAllWindows()

    def _generate_random_coordinate(self) -> Tuple[int, int]:
        x = random.randint(0, Config.CAMERA_WIDTH - 1)
        y = random.randint(0, Config.CAMERA_HEIGHT - 1)
        return (x, y)
