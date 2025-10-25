from flask import Flask, render_template, request
from flask_cors import CORS
import os
import time
from dotenv import load_dotenv
import asyncio
import cv2
import json
from threading import Thread
from flask_sock import Sock

from config import Config
from services.sound_mapper import SoundMapper
from services.sensor_ingestion import SensorIngestion

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
CORS(app)
sock = Sock(app)

# Initialize services
sound_mapper = SoundMapper()
sensor_ingestion = SensorIngestion()

# Connect sensor ingestion to sound mapper
sensor_ingestion.set_impact_callback(sound_mapper.process_impact)

# Store active WebSocket connections
ws_clients = []
drumstick_ws = None

@app.route('/')
def index():
    return {
        "status": "VODKA api running",
        "mode": {
            "camera": "MOCK" if Config.MOCK_CAMERA else "REAL",
            "detection": "MOCK" if Config.MOCK_DETECTION else "REAL",
            "coordinates": "MOCK" if Config.MOCK_COORDINATES else "REAL"
        },
        "sensor_connected": sensor_ingestion.is_connected()
    }

@sock.route('/drumstick')
def handle_websocket(ws):
    global drumstick_ws
    print('Drumstick connected via WebSocket')
    drumstick_ws = ws
    sensor_ingestion.on_connect("ws_client")

    # Broadcast to monitors
    broadcast_to_clients({'type': 'sensor_connected'})

    try:
        while True:
            message = ws.receive()
            if message is None:
                break

            # Parse JSON message
            try:
                data = json.loads(message)
                print(f"Received from drumstick: {data}")

                # Handle different message types
                msg_type = data.get('type', 'impact')  # Default to impact

                if msg_type == 'ping':
                    ws.send(json.dumps({'type': 'pong', 'timestamp': int(time.time() * 1000)}))

                elif msg_type == 'impact' or 'velocity' in data:
                    # Process impact
                    response = asyncio.run(sensor_ingestion.handle_message(json.dumps(data)))

                    if response:
                        # Send ack back to ESP32
                        ws.send(json.dumps(response))

                        # Broadcast to monitors
                        if response.get('type') == 'ack' and 'material' in response:
                            broadcast_to_clients({
                                'type': 'impact_processed',
                                'data': response
                            })

            except json.JSONDecodeError:
                print(f"Invalid JSON received: {message}")
            except Exception as e:
                print(f"Error processing message: {e}")

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        print('Drumstick disconnected')
        drumstick_ws = None
        sensor_ingestion.on_disconnect()
        broadcast_to_clients({'type': 'sensor_disconnected'})

@sock.route('/monitor')
def handle_monitor_websocket(ws):
    print('Monitor client connected')
    ws_clients.append(ws)

    try:
        ws.send(json.dumps({'type': 'connected', 'status': 'ok'}))
        while True:
            message = ws.receive()
            if message is None:
                break
    except:
        pass
    finally:
        if ws in ws_clients:
            ws_clients.remove(ws)
        print('Monitor client disconnected')

def broadcast_to_clients(data):
    disconnected = []
    for ws in ws_clients:
        try:
            ws.send(json.dumps(data))
        except:
            disconnected.append(ws)

    # Remove disconnected clients
    for ws in disconnected:
        if ws in ws_clients:
            ws_clients.remove(ws)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("VODKA Drumstick Server Starting")
    print("="*60)
    print(f"Mode Configuration:")
    print(f"  Camera:      {'MOCK' if Config.MOCK_CAMERA else 'REAL'}")
    print(f"  Detection:   {'MOCK' if Config.MOCK_DETECTION else 'REAL'}")
    print(f"  Coordinates: {'MOCK' if Config.MOCK_COORDINATES else 'REAL'}")
    print(f"\nMaterial Regions:")
    for i, (x_min, y_min, x_max, y_max, material) in enumerate(Config.MATERIAL_REGIONS):
        print(f"  {i+1}. ({x_min:3d},{y_min:3d}) → ({x_max:3d},{y_max:3d}): {material}")
    print("="*60)
    print(f"Server running on http://0.0.0.0:8080")
    print(f"WebSocket endpoints:")
    print(f"  /drumstick - ESP32 connection")
    print(f"  /monitor   - Frontend monitoring (optional)")
    print("="*60 + "\n")

    # TODO: Classify materials once at startup
    # Currently hardcoded in config.py
    # sound_mapper.cv_localizer.classify_materials_once()

    # Run server
    port = int(os.getenv('FLASK_PORT', 8080))

    try:
        app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
    finally:
        # Cleanup on shutdown
        sound_mapper.cleanup()
        print("\nServer stopped")
