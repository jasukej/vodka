"""
BLE Service for ESP32 Drumstick Communication
Replaces WebSocket with Bluetooth Low Energy
"""

import asyncio
import json
import logging
import time
from typing import Optional, Callable, Dict, Any
import threading
from dataclasses import dataclass

try:
    import bleak
    from bleak import BleakClient, BleakScanner
    from bleak.backends.characteristic import BleakGATTCharacteristic
    BLE_AVAILABLE = True
except ImportError:
    BLE_AVAILABLE = False
    print("⚠️  BLE not available. Install with: pip install bleak")

logger = logging.getLogger(__name__)

# BLE Service and Characteristic UUIDs (must match ESP32)
SERVICE_UUID = "12345678-1234-1234-1234-123456789abc"
IMPACT_CHAR_UUID = "87654321-4321-4321-4321-cba987654321"
STATUS_CHAR_UUID = "11111111-2222-3333-4444-555555555555"
CONFIG_CHAR_UUID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"

DEVICE_NAME = "VODKA-Drumstick"

@dataclass
class DrumstickStatus:
    connected: bool = False
    battery_level: float = 0.0
    total_hits: int = 0
    uptime: int = 0
    impact_threshold: float = 15.0
    last_seen: float = 0.0

class BLEDrumstickService:
    def __init__(self):
        if not BLE_AVAILABLE:
            raise ImportError("BLE support not available. Install bleak: pip install bleak")

        self.client: Optional[BleakClient] = None
        self.device_address: Optional[str] = None
        self.connected = False
        self.status = DrumstickStatus()

        # Callbacks
        self.on_impact_callback: Optional[Callable[[dict], None]] = None
        self.on_status_callback: Optional[Callable[[dict], None]] = None
        self.on_connect_callback: Optional[Callable[[], None]] = None
        self.on_disconnect_callback: Optional[Callable[[], None]] = None

        # Background tasks
        self._scan_task: Optional[asyncio.Task] = None
        self._connection_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info("BLE Drumstick Service initialized")

    def set_impact_callback(self, callback: Callable[[dict], None]):
        """Set callback for impact events"""
        self.on_impact_callback = callback

    def set_status_callback(self, callback: Callable[[dict], None]):
        """Set callback for status updates"""
        self.on_status_callback = callback

    def set_connect_callback(self, callback: Callable[[], None]):
        """Set callback for connection events"""
        self.on_connect_callback = callback

    def set_disconnect_callback(self, callback: Callable[[], None]):
        """Set callback for disconnection events"""
        self.on_disconnect_callback = callback

    async def start(self):
        """Start the BLE service"""
        if self._running:
            return

        self._running = True
        logger.info("🔵 Starting BLE Drumstick Service...")

        # Start scanning for devices
        self._scan_task = asyncio.create_task(self._scan_and_connect_loop())

        logger.info("🔍 Scanning for VODKA Drumstick...")

    async def stop(self):
        """Stop the BLE service"""
        self._running = False

        if self._scan_task:
            self._scan_task.cancel()

        if self._connection_task:
            self._connection_task.cancel()

        await self._disconnect()
        logger.info("🔴 BLE Drumstick Service stopped")

    async def _scan_and_connect_loop(self):
        """Main loop to scan for and connect to drumstick"""
        while self._running:
            try:
                if not self.connected:
                    await self._scan_for_drumstick()

                    if self.device_address:
                        await self._connect_to_drumstick()

                # Check connection health
                if self.connected and self.client:
                    try:
                        # Send ping to check if still connected
                        await self._send_config({"ping": True})
                    except Exception as e:
                        logger.warning(f"Connection health check failed: {e}")
                        await self._disconnect()

                await asyncio.sleep(5)  # Scan every 5 seconds if not connected

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scan loop: {e}")
                await asyncio.sleep(10)

    async def _scan_for_drumstick(self):
        """Scan for VODKA Drumstick device"""
        try:
            logger.info("🔍 Scanning for BLE devices...")

            devices = await BleakScanner.discover(timeout=10.0)

            for device in devices:
                if device.name == DEVICE_NAME:
                    logger.info(f"✅ Found VODKA Drumstick: {device.address}")
                    self.device_address = device.address
                    return

            logger.info("❌ VODKA Drumstick not found")

        except Exception as e:
            logger.error(f"Error scanning for devices: {e}")

    async def _connect_to_drumstick(self):
        """Connect to the drumstick device"""
        if not self.device_address:
            return

        try:
            logger.info(f"🔗 Connecting to drumstick at {self.device_address}...")

            self.client = BleakClient(self.device_address)
            await self.client.connect()

            # Subscribe to notifications
            await self.client.start_notify(IMPACT_CHAR_UUID, self._handle_impact_notification)
            await self.client.start_notify(STATUS_CHAR_UUID, self._handle_status_notification)

            self.connected = True
            self.status.connected = True
            self.status.last_seen = time.time()

            logger.info("🟢 Connected to VODKA Drumstick!")

            # Send initial configuration
            await self._send_initial_config()

            if self.on_connect_callback:
                self.on_connect_callback()

        except Exception as e:
            logger.error(f"Failed to connect to drumstick: {e}")
            await self._disconnect()

    async def _disconnect(self):
        """Disconnect from drumstick"""
        if self.client and self.connected:
            try:
                await self.client.disconnect()
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")

        self.connected = False
        self.status.connected = False
        self.client = None

        if self.on_disconnect_callback:
            self.on_disconnect_callback()

        logger.info("🔴 Disconnected from VODKA Drumstick")

    async def _handle_impact_notification(self, characteristic: BleakGATTCharacteristic, data: bytearray):
        """Handle impact data from drumstick"""
        try:
            json_str = data.decode('utf-8')
            impact_data = json.loads(json_str)

            logger.info(f"🥁 Impact received: {impact_data}")

            self.status.last_seen = time.time()

            if self.on_impact_callback:
                self.on_impact_callback(impact_data)

        except Exception as e:
            logger.error(f"Error handling impact notification: {e}")

    async def _handle_status_notification(self, characteristic: BleakGATTCharacteristic, data: bytearray):
        """Handle status updates from drumstick"""
        try:
            json_str = data.decode('utf-8')
            status_data = json.loads(json_str)

            logger.info(f"📊 Status received: {status_data}")

            # Update internal status
            self.status.last_seen = time.time()
            if 'total_hits' in status_data:
                self.status.total_hits = status_data['total_hits']
            if 'uptime' in status_data:
                self.status.uptime = status_data['uptime']
            if 'battery' in status_data:
                self.status.battery_level = status_data['battery']
            if 'threshold' in status_data:
                self.status.impact_threshold = status_data['threshold']

            if self.on_status_callback:
                self.on_status_callback(status_data)

        except Exception as e:
            logger.error(f"Error handling status notification: {e}")

    async def _send_config(self, config: Dict[str, Any]):
        """Send configuration to drumstick"""
        if not self.connected or not self.client:
            logger.warning("Cannot send config - not connected")
            return False

        try:
            config_json = json.dumps(config)
            await self.client.write_gatt_char(CONFIG_CHAR_UUID, config_json.encode('utf-8'))
            logger.info(f"📤 Config sent: {config}")
            return True
        except Exception as e:
            logger.error(f"Error sending config: {e}")
            return False

    async def _send_initial_config(self):
        """Send initial configuration after connection"""
        config = {
            "impact_threshold": 15.0,
            "calibrate": False
        }
        await self._send_config(config)

    # Public methods for configuration

    async def calibrate_drumstick(self):
        """Trigger drumstick calibration"""
        return await self._send_config({"calibrate": True})

    async def set_impact_threshold(self, threshold: float):
        """Set impact detection threshold"""
        return await self._send_config({"impact_threshold": threshold})

    async def reset_statistics(self):
        """Reset hit counter and statistics"""
        return await self._send_config({"reset_stats": True})

    def is_connected(self) -> bool:
        """Check if drumstick is connected"""
        return self.connected

    def get_status(self) -> DrumstickStatus:
        """Get current drumstick status"""
        return self.status

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        return {
            "connected": self.connected,
            "device_address": self.device_address,
            "device_name": DEVICE_NAME,
            "last_seen": self.status.last_seen,
            "uptime": self.status.uptime,
            "total_hits": self.status.total_hits,
            "battery_level": self.status.battery_level,
            "impact_threshold": self.status.impact_threshold
        }

# Thread-safe wrapper for use in Flask app
class BLEDrumstickServiceWrapper:
    def __init__(self):
        self.ble_service = BLEDrumstickService() if BLE_AVAILABLE else None
        self.loop = None
        self.thread = None
        self._running = False

    def start(self):
        """Start BLE service in background thread"""
        if not self.ble_service:
            logger.error("BLE not available")
            return False

        if self._running:
            return True

        self._running = True
        self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self.thread.start()
        logger.info("BLE service started in background thread")
        return True

    def stop(self):
        """Stop BLE service"""
        if not self._running:
            return

        self._running = False

        if self.loop and self.ble_service:
            # Schedule stop on the event loop
            asyncio.run_coroutine_threadsafe(self.ble_service.stop(), self.loop)

        if self.thread:
            self.thread.join(timeout=5.0)

        logger.info("BLE service stopped")

    def _run_event_loop(self):
        """Run asyncio event loop in background thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            self.loop.run_until_complete(self.ble_service.start())
            self.loop.run_forever()
        except Exception as e:
            logger.error(f"Error in BLE event loop: {e}")
        finally:
            self.loop.close()

    def set_impact_callback(self, callback):
        """Set impact callback"""
        if self.ble_service:
            self.ble_service.set_impact_callback(callback)

    def set_status_callback(self, callback):
        """Set status callback"""
        if self.ble_service:
            self.ble_service.set_status_callback(callback)

    def set_connect_callback(self, callback):
        """Set connect callback"""
        if self.ble_service:
            self.ble_service.set_connect_callback(callback)

    def set_disconnect_callback(self, callback):
        """Set disconnect callback"""
        if self.ble_service:
            self.ble_service.set_disconnect_callback(callback)

    def is_connected(self) -> bool:
        """Check if connected"""
        return self.ble_service.is_connected() if self.ble_service else False

    def get_status(self):
        """Get drumstick status"""
        return self.ble_service.get_status() if self.ble_service else None

    def get_connection_info(self):
        """Get connection info"""
        return self.ble_service.get_connection_info() if self.ble_service else {}

    def calibrate_drumstick(self):
        """Calibrate drumstick"""
        if self.ble_service and self.loop:
            asyncio.run_coroutine_threadsafe(
                self.ble_service.calibrate_drumstick(), self.loop
            )

    def set_impact_threshold(self, threshold: float):
        """Set impact threshold"""
        if self.ble_service and self.loop:
            asyncio.run_coroutine_threadsafe(
                self.ble_service.set_impact_threshold(threshold), self.loop
            )

    def reset_statistics(self):
        """Reset statistics"""
        if self.ble_service and self.loop:
            asyncio.run_coroutine_threadsafe(
                self.ble_service.reset_statistics(), self.loop
            )

# Global instance
ble_drumstick_service = BLEDrumstickServiceWrapper()