#!/usr/bin/env python3
import argparse
import json
import urllib.request
import sys

def dispatch(event: str, payload_str: str, endpoint: str = "http://localhost:8000/api/broadcast"):
    try:
        payload_data = json.loads(payload_str) if isinstance(payload_str, str) else payload_str
    except Exception as e:
        print(f"[UIDispatcher] Invalid JSON payload: {e}")
        sys.exit(1)

    envelope = {
        "event_type": event,
        "payload": payload_data
    }
    
    data_bytes = json.dumps(envelope).encode("utf-8")
    req = urllib.request.Request(endpoint, data=data_bytes, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=3) as resp:
            print(f"[UIDispatcher] Broadcasted event '{event}' to {endpoint} -> HTTP Status {resp.status}")
    except Exception as e:
        # Graceful fallback logging to stdout for terminal inspection
        print(f"[UIDispatcher Server Offline / Fallback] Event: {event}")
        print(json.dumps(envelope, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="UI & Telegram Telemetry Dispatcher CLI")
    parser.add_argument("--event", choices=["CHART_MARKER", "UPSERT_WIDGET", "TELEGRAM_ALERT", "SIGNAL_TRIGGERED"], required=True, help="Telemetry event type")
    parser.add_argument("--payload", required=True, help="JSON payload string")
    parser.add_argument("--endpoint", default="http://localhost:8000/api/broadcast", help="HTTP broadcast endpoint (default: http://localhost:8000/api/broadcast)")
    args = parser.parse_args()
    
    dispatch(args.event, args.payload, args.endpoint)
