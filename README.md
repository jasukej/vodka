# Virtual Online Drum Kit App (VODKA)

Transform any surface into a drum kit using computer vision and accelerometer data!

## System Architecture
```
┌─────────────┐
│  Drumstick  │
│ ESP32+MPU   │
└──────┬──────┘
       │ USB
       ↓
┌──────────────────┐      ┌────────────┐
│  Python Backend  │←────→│  Webcam    │
│  - Hit Detection │      │  (CV)      │
│  - Sound Engine  │      └────────────┘
└────────┬─────────┘
         │ WebSocket
         ↓
┌──────────────────┐
│   React Frontend │
│  - Visualization │
│  - Controls      │
└──────────────────┘
```

## Quick Start

### 1. Hardware Setup
See `firmware/esp32_sensor/README.md`

### 2. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration
python app.py
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. Upload Firmware
Open `firmware/esp32_sensor/esp32_sensor.ino` in Arduino IDE and upload to ESP32.

## Project Structure
```
virtual-drum-kit/
├── firmware/           # ESP32 code
├── backend/           # Python Flask server
│   ├── services/      # Core logic modules
│   ├── utils/         # Helper functions
│   └── app.py         # Main server
├── frontend/          # React web app
│   └── src/
│       ├── components/
│       └── services/
├── sounds/            # Audio samples
├── config/            # Configuration files
└── docs/              # Documentation
```

## Team Roles

- **Person 1:** Hardware + Sensor Integration
- **Person 2:** Computer Vision + ML
- **Person 3:** Web UI + Sound Engine

## Model Integration - YOLO/FastSAM

### 🚀 Quick Start: Test Locally (No Deployment)

Open http://localhost:5173 in your browser and click "Start Streaming".

### Model Options

**Option 1: Local YOLO (Development)**
```bash
pip install ultralytics
python app.py
```
- ✅ No deployment needed
- ✅ Real segmentation
- ✅ Fast iteration

**Option 2: Baseten (Production)**
```bash
# Deploy your model to Baseten
# Update .env with endpoint
python app.py
```
- ✅ GPU acceleration
- ✅ Scalable
- ✅ Production ready

### Architecture

- Webcam captures frames at 10fps
- Frame buffer keeps last 2 seconds
- Calibration runs: once, 2s after clicking "Start Streaming"
- Segments stored in memory for hit localization
- Hits map to nearest segment → drum pad

## Testing

### Hit Mapping & Segmentation Store Test
```bash
cd backend
python3 test/test_hit_mapping.py
```

Verifies:
- Segmentation store saves/retrieves segments
- Hit localizer maps coordinates to objects
- Object class names are properly associated

### Simulate Hits via Browser Console
```javascript
socketService.emit('simulate_hit', {
  intensity: 500,
  timestamp: Date.now()
});
```

## Troubleshooting

### ESP32 not detected
- Check USB cable (must support data transfer)
- Install CH340 drivers if needed
- Try different USB port

### No sound playing
- Check `sounds/` directory has .wav files
- Verify pygame.mixer initialized correctly
- Check system audio isn't muted

### High latency
- Reduce webcam resolution
- Disable CV and use accelerometer only
- Check network latency if using hosted model
EOF