import urllib.request
import urllib.error
import json
import time
import sys

API_URL = "http://127.0.0.1:8000"

WORLD_FILE = "worlds/rescue_orch.wbt"

def result_parser(content, def_name):
    """Simple parser to find 'DEF <def_name> Solid/Transform { translation x y z'."""
    try:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if f"DEF {def_name}" in line:
                # Look ahead for translation
                for j in range(i, min(i+10, len(lines))):
                    if "translation" in lines[j]:
                        parts = lines[j].strip().split()
                        # format: translation x y z
                        if len(parts) >= 4:
                            return {
                                "x": float(parts[1]),
                                "y": float(parts[2]),
                                "z": float(parts[3])
                            }
    except Exception as e:
        print(f"Error parsing world file: {e}")
    return None

def get_kitchen_location():
    """Fetch Kitchen location (FIRE_VISUAL) from world file."""
    try:
        with open(WORLD_FILE, 'r') as f:
            content = f.read()
        
        # We use FIRE_VISUAL as the text marker for the Kitchen incident
        coords = result_parser(content, "FIRE_VISUAL")
        if coords:
            log(f"Dynamic Location Parsed: Kitchen (FIRE_VISUAL) -> {coords}", "📂")
            return coords
        else:
            log("Could not find FIRE_VISUAL in world file. Using fallback.", "⚠️")
    except FileNotFoundError:
        log("World file not found. Using fallback.", "⚠️")
        
    return {"x": 1.63, "y": 0.92, "z": 1.15}

KITCHEN_COORDS = get_kitchen_location()


def get(endpoint):
    try:
        with urllib.request.urlopen(f"{API_URL}{endpoint}") as response:
            return json.loads(response.read().decode())
    except Exception as e:
        return None

def post(endpoint, data=None):
    try:
        req = urllib.request.Request(f"{API_URL}{endpoint}", method="POST")
        req.add_header('Content-Type', 'application/json')
        body = json.dumps(data).encode('utf-8') if data else None
        with urllib.request.urlopen(req, data=body) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode()}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def wait_for_backend():
    log("Waiting for backend...", "⏳")
    for i in range(10):
        if get("/"):
            log("Backend connected!", "✅")
            return
        time.sleep(1)
    log("Backend unreachable.", "❌")
    sys.exit(1)

def run_demo():
    wait_for_backend()

    log("Starting KITCHEN RESCUE DEMO", "🚀")

    # Step 1: Start Mission
    log("Initializing Mission...", "1️⃣")
    res = post("/mission/start")
    if res:
        log("Mission Started.", "✅")
    else:
        log("Mission Start Failed.", "⚠️")

    # Step 2: Fly Drone to Kitchen
    log(f"Moving Drone to Kitchen at {KITCHEN_COORDS}", "2️⃣")
    # Using action endpoint
    post("/mavic/takeoff")
    time.sleep(2)
    # Simulate move
    log("Drone Hovering near Kitchen.", "🚁")

    # Step 3: Trigger Alarm (Fire Detected)
    log("Triggering FIRE ALARM at Kitchen...", "3️⃣")
    incident = {
        "type": "fire",
        "location": KITCHEN_COORDS,
        "severity": "critical",
        "description": "Visual confirmation: Fire in Kitchen by Drone"
    }
    
    res = post("/mission/incident/report", data=incident)
    if res:
        analysis = res.get('ai_analysis', {}).get('analysis', 'Processing...')
        # Handle if analysis is a dict or string
        if isinstance(analysis, dict):
            analysis = json.dumps(analysis)
        log(f"Incident Reported! AI Analysis: {analysis[:100]}...", "🔥")
        log("Waiting for AI to assign robots...", "🤖")
    else:
        log("Failed to report incident.", "❌")
        return

    # Step 4: Monitor Robot Assignment (Tiago1 should go)
    log("Monitoring Robot Assignments...", "4️⃣")
    target_assigned = False
    max_retries = 20
    
    while not target_assigned and max_retries > 0:
        status = get("/mission/status")
        if not status:
            time.sleep(1)
            continue
            
        robots = status.get("robots", {})
        tiago1 = robots.get(ROBOT_NAME)
        
        # Check if task contains 'fire' or 'kitchen'
        task = tiago1.get("task", "").lower() if tiago1 else ""
        if tiago1 and task and ("fire" in task or "kitchen" in task):
            log(f"AI Assigned {ROBOT_NAME} to: {tiago1['task']}", "🎯")
            target_assigned = True
        else:
            time.sleep(1)
            max_retries -= 1
            print(".", end="", flush=True)
    
    print("") # Newline
    if not target_assigned:
        log("AI timed out on assignment. Proceeding anyway...", "⚠️")
        # return # Optional: Stop or continue? Let's continue for demo sake.

    # User Step 5: Simulate Extinguish
    log(f"Simulating {ROBOT_NAME} travel to Kitchen...", "🚚")
    time.sleep(5) 
    
    log(f"{ROBOT_NAME} Reached Kitchen! Starting Extinguish Protocol...", "🧯")
    
    # Update Status: Extinguishing
    post(f"/tiago/{ROBOT_NAME}/status", data={
        "status": "extinguishing",
        "position": KITCHEN_COORDS,
        "step_completed": False
    })
    
    time.sleep(3)
    
    log(f"{ROBOT_NAME}: Fire Extinguished! Reporting Done.", "✅")
    
    # Update Status: Idle (Complete)
    post(f"/tiago/{ROBOT_NAME}/status", data={
        "status": "idle",
        "step_completed": True
    })
    
    log("Robot 1 Task Complete. Waiting for AI to assign Robot 2...", "🔄")
    
    # Trigger dependent task (Cleanup)
    cleanup_incident = {
        "type": "cleanup",
        "location": KITCHEN_COORDS,
        "severity": "medium",
        "description": "Fire extinguished. Debris removal required."
    }
    post("/mission/incident/report", data=cleanup_incident)
    
    log("Reported 'Cleanup Required'. Checking for Robot 2 assignment...", "🧹")
    
    # Monitor for any other robot (tiago2/3) getting a task
    # ... (omitted for brevity, but could add loop)
    
    log("DEMO SEQUENCE COMPLETE", "🏁")

if __name__ == "__main__":
    run_demo()
