from typing import List, Dict, Any
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.widget_state: Dict[str, Any] = {}
        self.signal_history: List[Dict[str, Any]] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Replay current state to new clients
        for widget in self.widget_state.values():
            await websocket.send_json({
                "event_type": "UPSERT_WIDGET",
                "payload": widget
            })

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        # Update internal state if widget upsert
        event_type = message.get("event_type")
        payload = message.get("payload", {})
        
        if event_type == "UPSERT_WIDGET" and isinstance(payload, dict):
            widget_id = payload.get("id", payload.get("title", "default"))
            self.widget_state[widget_id] = payload
        elif event_type == "SIGNAL_TRIGGERED" and isinstance(payload, dict):
            self.signal_history.append(payload)

        # Broadcast to all connected WebSockets
        to_remove = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                to_remove.append(connection)
                
        for dead_conn in to_remove:
            self.disconnect(dead_conn)

manager = ConnectionManager()
