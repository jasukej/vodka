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
    
    SOUNDS_DIR = '../sounds'
    MODELS_DIR = '../models'
    CONFIG_DIR = '../config'

