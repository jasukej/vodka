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
    MOCK_CAMERA = os.getenv('MOCK_CAMERA', 'false').lower() == 'true'
    MOCK_DETECTION = os.getenv('MOCK_DETECTION', 'false').lower() == 'true'
    MOCK_COORDINATES = os.getenv('MOCK_COORDINATES', 'false').lower() == 'true'
    SHOW_DEBUG_WINDOW = os.getenv('SHOW_DEBUG_WINDOW', 'false').lower() == 'true'

    DRUMSTICK_MODEL_SIZE = os.getenv('DRUMSTICK_MODEL_SIZE', 'medium')

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

    # Legacy sound mapping (for backward compatibility)
    # backend/config.py -> ../sounds (go up one level from backend)
    backend_dir = os.path.dirname(__file__)
    repo_root = os.path.dirname(backend_dir)
    sounds_dir = os.path.join(repo_root, "sounds")
    SOUND_MAPPING = {
        "wood": os.path.join(sounds_dir, "bass.ogg"),
        "metal": os.path.join(sounds_dir, "iron_xylophone.ogg"),
        "glass": os.path.join(sounds_dir, "hat.ogg"),
        "plastic": os.path.join(sounds_dir, "snare.ogg"),
        "default": os.path.join(sounds_dir, "harp.ogg")
    }
    
    # Drum pad to sound mapping (based on detected material class)
    DRUM_SOUND_MAPPING = {
        "snare": os.path.join(sounds_dir, "snare.ogg"),
        "kick": os.path.join(sounds_dir, "bass.ogg"),
        "hihat": os.path.join(sounds_dir, "hat.ogg"),
        "hi-hat": os.path.join(sounds_dir, "hat.ogg"),
        "cymbal": os.path.join(sounds_dir, "iron_xylophone.ogg"),
        "tom": os.path.join(sounds_dir, "bass.ogg"),
        "default": os.path.join(sounds_dir, "harp.ogg")
    }
    
    # Material to drum sound mapping
    MATERIAL_TO_DRUM = {
        # Organic materials -> Snare (dry, snappy sound)
        "hide": "snare",
        "skin": "snare",
        "fur": "snare",
        "hair": "snare",
        "foliage": "snare",
        "bone": "snare",
        "wicker": "snare",
        "carpet": "snare",
        "fabric": "snare",
        
        # Hard, resonant materials -> Kick (deep, bass sound)
        "wood": "kick",
        "treewood": "kick",
        "concrete": "kick",
        "stone": "kick",
        "polishedstone": "kick",
        "brick": "kick",
        "tile": "kick",
        "ceramic": "kick",
        "engineeredstone": "kick",
        "asphalt": "kick",
        
        # Metallic materials -> Cymbal (bright, shimmering sound)
        "metal": "cymbal",
        "gemstone": "cymbal",
        "pearl": "cymbal",
        
        # Glass/crystal materials -> Hi-Hat (crisp, sharp sound)
        "glass": "hihat",
        "mirror": "hihat",
        "ice": "hihat",
        "clearplastic": "hihat",
        
        # Soft plastic materials -> Tom (medium, rounded sound)
        "plastic": "tom",
        "rubber": "tom",
        "sponge": "tom",
        "ceilingtile": "tom",
        "styrofoam": "tom",
        "soap": "tom",
        
        # Paper/cardboard materials -> Snare (dry, crackling sound)
        "paper": "snare",
        "cardboard": "snare",
        "cork": "snare",
        
        # Other materials -> Default based on hardness
        "water": "hihat",
        "liquid": "hihat",
        "fire": "cymbal",
        "food": "tom",
        "photograph": "snare",
        "wallpaper": "snare",
        "paint": "tom",
        "wax": "tom",
        "chalkboard": "snare",
        "whiteboard": "snare",
        "fiberglass": "tom",
        
        # Additional materials from YOLO model
        "leather": "snare",
        "other": "snare",
        "sky": "hihat",
        
        # Catch-all for unknown materials
        "none": "default",
        "clutter": "tom",
        "icannottell": "tom",
        "notonlist": "default",
        "badpolygon": "default",
        "multiplematerials": "snare"
    }
