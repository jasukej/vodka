import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SERIAL_PORT = os.getenv('SERIAL_PORT', '/dev/cu.usbserial-0001')
    SERIAL_BAUDRATE = int(os.getenv('SERIAL_BAUDRATE', 115200))

    USE_HOSTED_MODEL = os.getenv('USE_HOSTED_MODEL', 'false').lower() == 'true'
    HOSTED_MODEL_URL = os.getenv('HOSTED_MODEL_URL', '')
    HOSTED_MODEL_API_KEY = os.getenv('HOSTED_MODEL_API_KEY', '')

    SAMPLE_RATE = int(os.getenv('SAMPLE_RATE', 44100))
    BUFFER_SIZE = int(os.getenv('BUFFER_SIZE', 512))

    HIT_THRESHOLD = 2.5  # g-force
    HIT_COOLDOWN = 0.1   # seconds
    
    CALIBRATION_INTERVAL = 5
    CALIBRATION_INITIAL_DELAY = 5
    # unused for now
    FRAME_BUFFER_DURATION = 2
    FRAME_BUFFER_MAX_FRAMES = 20
    
    SOUNDS_DIR = '../sounds'
    MODELS_DIR = '../models'
    CONFIG_DIR = '../config'

    # ============ CAMERA & DETECTION CONFIG ============
    # Mock modes for development/testing
    MOCK_CAMERA = os.getenv('MOCK_CAMERA', 'true').lower() == 'true'
    MOCK_DETECTION = os.getenv('MOCK_DETECTION', 'true').lower() == 'true'
    MOCK_COORDINATES = os.getenv('MOCK_COORDINATES', 'true').lower() == 'true'
    SHOW_DEBUG_WINDOW = os.getenv('SHOW_DEBUG_WINDOW', 'false').lower() == 'true'

    # Camera settings
    CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', 0))
    CAMERA_WIDTH = int(os.getenv('CAMERA_WIDTH', 640))
    CAMERA_HEIGHT = int(os.getenv('CAMERA_HEIGHT', 480))
    CAMERA_FPS = int(os.getenv('CAMERA_FPS', 60))

    # Material regions (x_min, y_min, x_max, y_max, material_name)
    # Coordinates are in pixels relative to camera resolution
    MATERIAL_REGIONS = [
        (0, 0, 320, 240, "wood"),           # Top-left quadrant
        (320, 0, 640, 240, "metal"),        # Top-right quadrant
        (0, 240, 320, 480, "glass"),        # Bottom-left quadrant
        (320, 240, 640, 480, "plastic"),    # Bottom-right quadrant
    ]

    # Sound mapping
    SOUND_MAPPING = {
        "wood": "sounds/bass.ogg",
        "metal": "sounds/iron_xylophone.ogg",
        "glass": "sounds/hat.ogg",
        "plastic": "sounds/snare.ogg",
        "default": "sounds/harp.ogg"
    }
