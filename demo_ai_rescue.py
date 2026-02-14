
"""
AI Rescue Mission Demo - Viewer
This script triggers the DEMO MODE in the backend and visualizes the progress.
Run this script OR click "Start Mission" in the frontend.
"""
import urllib.request
import json
import time
import sys

API_URL = "http://127.0.0.1:8000"

def log(msg, emoji="ℹ️"):
    print(f"{emoji} {msg}")

def get(endpoint):
    try:
        with urllib.request.urlopen(f"{API_URL}{endpoint}") as response:
            return json.loads(response.read().decode())
    except Exception:
        return None

def post(endpoint, data=None):
    try:
        req = urllib.request.Request(f"{API_URL}{endpoint}", method="POST")
        req.add_header('Content-Type', 'application/json')
        body = json.dumps(data).encode('utf-8') if data else None
        with urllib.request.urlopen(req, data=body) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    log("Connecting to Rescue Backend...", "📡")
    if not get("/"):
        log("Backend unreachable. Ensure './run.bat' is running.", "❌")
        sys.exit(1)

    log("Starting KITCHEN RESCUE DEMO (Backend Orchestrated)", "🚀")
    
    # 1. Trigger Demo via Start Mission
    res = post("/mission/start")
    if res:
        log("Mission Started & Demo Sequence Triggered!", "✅")
    else:
        log("Failed to start mission.", "❌")
        return

    # 2. Passive Monitoring Loop
    log("Monitoring Mission Progress...", "👀")
    
    last_status_summary = ""
    
    try:
        while True:
            status = get("/mission/status")
            if not status:
                time.sleep(1)
                continue
            
            # Simple summarization for changes
            robots = status.get("robots", {})
            incidents = status.get("incidents", {}).get("total", 0)
            
            summary = []
            if incidents > 0:
                summary.append(f"🔥 Incidents: {incidents}")
            
            for r_id, r_data in robots.items():
                if r_data.get("task"):
                    task = r_data["task"]
                    state = r_data["status"]
                    summary.append(f"🤖 {r_id}: {state} ({task})")
            
            current_summary = " | ".join(summary)
            if current_summary != last_status_summary:
                print(f"Update: {current_summary}")
                last_status_summary = current_summary
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        log("Monitoring stopped.", "🛑")

if __name__ == "__main__":
    main()
