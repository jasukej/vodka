from flask import Flask, render_template, request
from flask_cors import CORS
import os
import time
import logging
from dotenv import load_dotenv
import asyncio
import cv2
import json
from threading import Thread
from flask_sock import Sock
from flask_socketio import SocketIO, emit

from config import Config
from services.sound_mapper import SoundMapper
from services.sensor_ingestion import SensorIngestion
from services.model_service import model_service
from services.segmentation_store import segmentation_store
from services.frame_buffer import frame_buffer
from services.hit_localizer import hit_localizer
from services.drumstick_detector import drumstick_detector

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
CORS(app)
sock = Sock(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize services
sound_mapper = SoundMapper()
sensor_ingestion = SensorIngestion()

async def handle_esp32_hit(impact_data: dict):
    """Handle hit detection from ESP32 sensor and trigger vision-based localization"""
    try:
        timestamp = impact_data.get('timestamp', int(time.time() * 1000))
        velocity = impact_data.get('velocity', 0)
        magnitude = impact_data.get('magnitude', 0)
        
        # Calculate intensity from velocity (normalize to 0-1 range)
        intensity = min(velocity / 100.0, 1.0) if velocity > 0 else 0.5
        
        logger.info(f'🥁 ESP32 HIT DETECTED: velocity={velocity}, magnitude={magnitude}, intensity={intensity:.2f}')
        
        # Trigger the same logic as simulate_hit
        if not segmentation_store.is_calibrated():
            logger.warning('System not calibrated - cannot localize hit')
            return
        
        latest_frame = frame_buffer.get_latest_frame()
        if not latest_frame:
            logger.warning('No frame available in buffer')
            return
        
        frame_timestamp = latest_frame.get('timestamp', 0)
        frame_data_size = len(latest_frame.get('frame', ''))
        frame_data_hash = hash(latest_frame.get('frame', '')) % 1000000
        logger.info(f'📸 Using frame from buffer: timestamp={frame_timestamp:.3f}, size={frame_data_size} bytes, hash={frame_data_hash}')
        
        segments = segmentation_store.get_segments()
        segment_count = len(segments.get('segments', []))
        logger.info(f'Using calibration with {segment_count} segments')

        logger.info('🥢 Running YOLOv8nano inference to detect drumstick...')
        hit_result = hit_localizer.localize_hit(
            latest_frame,
            segments,
            timestamp / 1000.0,
            None
        )
        
        if hit_result:
            drum = hit_result['drum_pad']
            conf = hit_result['confidence']
            pos = hit_result['position']
            segment_id = hit_result.get('segment_id', -1)
            bbox = hit_result.get('bbox', [])
            
            segment_list = segments.get('segments', [])
            class_name = 'unknown'
            if segment_id >= 0 and segment_id < len(segment_list):
                class_name = segment_list[segment_id].get('class_name', 'unknown')
            
            logger.info(f'HIT LOCALIZED:')
            logger.info(f'   Object: {class_name.upper()}')
            logger.info(f'   Drum Pad: {drum.upper()}')
            logger.info(f'   Confidence: {conf:.2f}')
            logger.info(f'   Position: ({pos.get("x", 0):.0f}, {pos.get("y", 0):.0f})')
            
            # Play sound based on detected drum pad class
            sound_mapper.audio_player.play_drum_sound(class_name, intensity)
            
            # Emit to connected clients via SocketIO
            socketio.emit('hit_localized', {
                'status': 'success',
                'drum_pad': drum,
                'position': pos,
                'confidence': conf,
                'intensity': intensity,
                'timestamp': timestamp,
                'segment_id': segment_id,
                'bbox': bbox,
                'class_name': class_name,
                'drumstick_position': hit_result.get('drumstick_position'),
                'source': 'esp32'
            })
        else:
            logger.error('Hit localization failed')
        
        logger.info('=' * 70)
        
    except Exception as e:
        logger.error(f'Error handling ESP32 hit: {e}')
        import traceback
        traceback.print_exc()

# Connect sensor ingestion callbacks
sensor_ingestion.set_hit_detected_callback(handle_esp32_hit)

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

@socketio.on('video_frame')
def handle_video_frame(data):
    timestamp = data.get('timestamp')
    frame_data = data.get('frame')

    if frame_data:
        frame_timestamp = timestamp / 1000.0 if timestamp else None
        frame_buffer.add_frame(frame_data, frame_timestamp)
        buffer_size = frame_buffer.get_buffer_size()
        logger.info(f'📸 Frame buffered: timestamp={frame_timestamp:.3f}, size={len(frame_data)} bytes, buffer={buffer_size} frames')
    else:
        logger.warning('Received video frame without frame data')

@socketio.on('calibrate_frame')
def handle_calibrate_frame(data):
    frame_data = data.get('frame')
    timestamp = data.get('timestamp')

    if not frame_data:
        logger.error('Calibrate frame called without frame data')
        emit('calibration_result', {
            'status': 'error',
            'message': 'No frame data provided',
            'timestamp': timestamp
        })
        return

    frame_size = len(frame_data)
    logger.info('=' * 70)
    logger.info(f'CALIBRATION STARTED (frame size: {frame_size} bytes)')
    logger.info('=' * 70)

    segmentation_result = model_service.segment_frame(frame_data)

    if segmentation_result and segmentation_result.get('success'):
        segment_count = segmentation_result.get('count', 0)
        segments = segmentation_result.get('segments', [])

        logger.info(f'Segmentation complete: {segment_count} objects detected')

        if segment_count > 0:
            logger.info('📊 Detected segments:')
            for i, seg in enumerate(segments[:5]):
                bbox = seg.get('bbox', [0, 0, 0, 0])
                conf = seg.get('confidence', 0)
                cls = seg.get('class', -1)
                class_name = seg.get('class_name', 'unknown')
                logger.info(f'   #{i}: {class_name.upper()} - bbox=({bbox[0]:3d}, {bbox[1]:3d}, {bbox[2]:3d}, {bbox[3]:3d}), conf={conf:.2f}')
            if len(segments) > 5:
                logger.info(f'   ... and {len(segments) - 5} more')

        segmentation_store.store_segments(segmentation_result, timestamp / 1000.0 if timestamp else None)
        logger.info(f'Segments stored in memory')

        emit('calibration_result', {
            'status': 'success',
            'segment_count': segment_count,
            'timestamp': timestamp,
            'message': f"Calibrated with {segment_count} segments",
            'segments': [
                {
                    'id': seg.get('id'),
                    'bbox': seg.get('bbox'),
                    'confidence': seg.get('confidence'),
                    'class': seg.get('class'),
                    'class_name': seg.get('class_name', 'unknown')
                }
                for seg in segments
            ]
        })
        logger.info(f'CALIBRATION SUCCESS - Ready for hit detection')
        logger.info('=' * 70)
    else:
        logger.error('Segmentation failed or returned no results')
        emit('calibration_result', {
            'status': 'error',
            'message': 'Failed to segment frame',
            'timestamp': timestamp
        })
        logger.error('=' * 70)

@socketio.on('simulate_hit')
def handle_simulate_hit(data):
    hit_timestamp = data.get('timestamp', 0) / 1000.0
    intensity = data.get('intensity', 1.0)
    position = data.get('position')

    logger.info('🥁 ' + '=' * 68)
    logger.info(f'HIT DETECTED (intensity: {intensity:.2f})')
    if position:
        logger.info(f'   Position: ({position.get("x", 0)}, {position.get("y", 0)})')

    if not segmentation_store.is_calibrated():
        logger.warning('System not calibrated - cannot localize hit')
        emit('hit_localized', {
            'status': 'error',
            'message': 'System not calibrated'
        })
        logger.info('=' * 70)
        return

    latest_frame = frame_buffer.get_latest_frame()
    if not latest_frame:
        logger.warning('No frame available in buffer')
        emit('hit_localized', {
            'status': 'error',
            'message': 'No frame available'
        })
        logger.info('=' * 70)
        return
    
    # TODO: delete later
    frame_timestamp = latest_frame.get('timestamp', 0)
    frame_data_size = len(latest_frame.get('frame', ''))
    frame_data_hash = hash(latest_frame.get('frame', '')) % 1000000  # Short hash for logging
    logger.info(f'📸 Using frame from buffer: timestamp={frame_timestamp:.3f}, size={frame_data_size} bytes, hash={frame_data_hash}')
    
    segments = segmentation_store.get_segments()
    segment_count = len(segments.get('segments', []))
    logger.info(f'Using calibration with {segment_count} segments')

    hit_result = hit_localizer.localize_hit(
        latest_frame,
        segments,
        hit_timestamp,
        None  # no manual pos: use YOLOv8nano detection
    )

    if hit_result:
        drum = hit_result['drum_pad']
        conf = hit_result['confidence']
        pos = hit_result['position']
        segment_id = hit_result.get('segment_id', -1)
        bbox = hit_result.get('bbox', [])

        segment_list = segments.get('segments', [])
        class_name = 'unknown'
        if segment_id >= 0 and segment_id < len(segment_list):
            class_name = segment_list[segment_id].get('class_name', 'unknown')

        logger.info(f'HIT LOCALIZED:')
        logger.info(f'   Object: {class_name.upper()}')
        logger.info(f'   Drum Pad: {drum.upper()}')
        logger.info(f'   Confidence: {conf:.2f}')
        logger.info(f'   Position: ({pos.get("x", 0):.0f}, {pos.get("y", 0):.0f})')
        
        # Play sound based on detected drum pad class
        sound_mapper.audio_player.play_drum_sound(class_name, intensity)
        
        emit('hit_localized', {
            'status': 'success',
            'drum_pad': drum,
            'position': pos,
            'confidence': conf,
            'intensity': intensity,
            'timestamp': data.get('timestamp'),
            'segment_id': segment_id,
            'bbox': bbox,
            'class_name': class_name,
            'drumstick_position': hit_result.get('drumstick_position'),
            'source': 'manual'
        })
    else:
        logger.error('Hit localization failed')
        emit('hit_localized', {
            'status': 'error',
            'message': 'Failed to localize hit'
        })

    logger.info('=' * 70)

@socketio.on('detect_drumstick')
def handle_detect_drumstick(data):
    frame_data = data.get('frame')
    timestamp = data.get('timestamp')
    confidence_threshold = data.get('confidence', 0.15)
    
    if not frame_data:
        logger.error('Drumstick detection called without frame data')
        emit('drumstick_detected', {
            'status': 'error',
            'message': 'No frame data provided',
            'timestamp': timestamp
        })
        return
    
    logger.info('🥢 ' + '=' * 68)
    logger.info(f'DRUMSTICK DETECTION STARTED (confidence: {confidence_threshold})')
    logger.info('=' * 70)
    
    detection_result = drumstick_detector.detect_drumsticks(frame_data, confidence_threshold)
    
    if detection_result and detection_result.get('success'):
        detections = detection_result.get('detections', [])
        detection_count = len(detections)
        
        logger.info(f'Detection complete: {detection_count} drumstick(s) detected')
        
        if detection_count > 0:
            logger.info('🥢 Detected drumsticks:')
            for i, det in enumerate(detections):
                bbox = det.get('bbox', [0, 0, 0, 0])
                conf = det.get('confidence', 0)
                class_name = det.get('class_name', 'unknown')
                center = det.get('center', {'x': 0, 'y': 0})
                logger.info(f'   #{i}: {class_name.upper()} - bbox=({bbox[0]:3d}, {bbox[1]:3d}, {bbox[2]:3d}, {bbox[3]:3d}), center=({center["x"]:3d}, {center["y"]:3d}), conf={conf:.2f}')
        
        emit('drumstick_detected', {
            'status': 'success',
            'detection_count': detection_count,
            'timestamp': timestamp,
            'message': f"Detected {detection_count} drumstick(s)",
            'detections': [
                {
                    'id': det.get('id'),
                    'bbox': det.get('bbox'),
                    'confidence': det.get('confidence'),
                    'class': det.get('class'),
                    'class_name': det.get('class_name', 'unknown'),
                    'center': det.get('center'),
                    'area': det.get('area')
                }
                for det in detections
            ]
        })
        logger.info(f'DRUMSTICK DETECTION SUCCESS')
        logger.info('=' * 70)
    else:
        logger.error('Drumstick detection failed or returned no results')
        emit('drumstick_detected', {
            'status': 'error',
            'message': 'Failed to detect drumsticks',
            'timestamp': timestamp
        })
        logger.error('=' * 70)

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
        socketio.run(app, host='0.0.0.0', port=port, debug=True, use_reloader=False)
    finally:
        # Cleanup on shutdown
        sound_mapper.cleanup()
        print("\nServer stopped")
