from typing import Optional, Callable, Awaitable
import json


class SensorIngestion:

    def __init__(self):
        self.connected_client = None
        self.on_impact_callback: Optional[Callable[[dict], Awaitable[dict]]] = None

    def set_impact_callback(self, callback: Callable[[dict], Awaitable[dict]]):
        self.on_impact_callback = callback

    def parse_sensor_message(self, raw_message: str) -> Optional[dict]:
        try:
            message = json.loads(raw_message)
            return message
        except json.JSONDecodeError as e:
            print(f"SensorIngestion: Failed to parse message: {e}")
            return None

    async def handle_message(self, raw_message: str, websocket=None) -> Optional[dict]:
        message = self.parse_sensor_message(raw_message)

        if message is None:
            return {"type": "error", "message": "Invalid message format"}

        msg_type = message.get("type")

        if msg_type == "impact":
            # Process impact through callback
            if self.on_impact_callback:
                result = await self.on_impact_callback(message)

                if result:
                    # Send acknowledgment
                    return {
                        "type": "ack",
                        "material": result["material"],
                        "position": result["position"],
                        "velocity": result["velocity"]
                    }
            return {"type": "ack", "status": "received"}

        elif msg_type == "ping":
            # Heartbeat
            return {"type": "pong"}

        elif msg_type == "calibration":
            # TODO: Handle calibration requests
            return {"type": "calibration_ack", "status": "not_implemented"}

        else:
            return {"type": "error", "message": f"Unknown message type: {msg_type}"}

    def on_connect(self, websocket):
        self.connected_client = websocket
        print("Drumstick sensor connected!")

    def on_disconnect(self):
        self.connected_client = None
        print("Drumstick sensor disconnected")

    def is_connected(self) -> bool:
        return self.connected_client is not None
