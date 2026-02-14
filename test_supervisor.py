"""Test script for supervisor control endpoints."""

import requests
import time
import json

API_URL = "http://127.0.0.1:8000"


def print_section(title):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_endpoint(method, endpoint, data=None, description=""):
    """Test an API endpoint."""
    url = f"{API_URL}{endpoint}"
    print(f"🧪 {description}")
    print(f"   {method} {endpoint}")
    
    try:
        if method == "GET":
            resp = requests.get(url, timeout=2)
        elif method == "POST":
            resp = requests.post(url, json=data, timeout=2)
        elif method == "DELETE":
            resp = requests.delete(url, timeout=2)
        else:
            print(f"   ❌ Unknown method: {method}")
            return False
        
        if resp.status_code == 200:
            print(f"   ✅ Success: {resp.json()}")
            return True
        else:
            print(f"   ❌ Failed: {resp.status_code} - {resp.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Error: {e}")
        return False


def main():
    print("\n🚀 SUPERVISOR CONTROL API TEST SUITE")
    print(f"API URL: {API_URL}")
    
    # Test 1: Position Control
    print_section("1. POSITION CONTROL (TELEPORT)")
    
    test_endpoint("POST", "/supervisor/teleport", {
        "target": "mavic",
        "position": {"x": 0, "y": 0, "z": 2.0}
    }, "Teleport Mavic to (0, 0, 2)")
    time.sleep(0.5)
    
    test_endpoint("POST", "/supervisor/teleport", {
        "target": "tiago1",
        "position": {"x": 1.0, "y": 0, "z": 0.095}
    }, "Teleport Tiago 1 to (1, 0, 0.095)")
    time.sleep(0.5)
    
    test_endpoint("POST", "/supervisor/teleport", {
        "target": "tiago2",
        "position": {"x": 2.0, "y": 0, "z": 0.095}
    }, "Teleport Tiago 2 to (2, 0, 0.095)")
    time.sleep(0.5)
    
    # Test 2: Velocity Control
    print_section("2. VELOCITY CONTROL")
    
    test_endpoint("POST", "/supervisor/velocity", {
        "target": "mavic",
        "velocity": {"vx": 1.0, "vy": 0, "vz": 0, "wx": 0, "wy": 0, "wz": 0}
    }, "Set Mavic velocity: forward at 1 m/s")
    time.sleep(0.5)
    
    test_endpoint("POST", "/supervisor/velocity", {
        "target": "tiago1",
        "velocity": {"vx": 0.5, "vy": 0, "vz": 0, "wx": 0, "wy": 0, "wz": 0}
    }, "Set Tiago 1 velocity: forward at 0.5 m/s")
    time.sleep(0.5)
    
    # Test 3: Stop Commands
    print_section("3. STOP COMMANDS")
    
    test_endpoint("POST", "/supervisor/stop/mavic", None, "Stop Mavic")
    time.sleep(0.5)
    
    test_endpoint("POST", "/supervisor/stop/tiago1", None, "Stop Tiago 1")
    time.sleep(0.5)
    
    test_endpoint("POST", "/supervisor/stop_all", None, "Stop all robots")
    time.sleep(0.5)
    
    # Test 4: Rotation Control
    print_section("4. ROTATION CONTROL")
    
    test_endpoint("POST", "/supervisor/rotate", {
        "target": "mavic",
        "rotation": {"axis_x": 0, "axis_y": 0, "axis_z": 1, "angle": 1.5708}
    }, "Rotate Mavic 90° around Z-axis")
    time.sleep(0.5)
    
    test_endpoint("POST", "/supervisor/rotate", {
        "target": "tiago1",
        "rotation": {"axis_x": 0, "axis_y": 0, "axis_z": 1, "angle": 3.14159}
    }, "Rotate Tiago 1 180° around Z-axis")
    time.sleep(0.5)
    
    # Test 5: Formation Commands
    print_section("5. FORMATION COMMANDS")
    
    test_endpoint("POST", "/supervisor/formation", {
        "formation_type": "line",
        "center_x": 0,
        "center_y": 0,
        "z": 0.095,
        "spacing": 2.0
    }, "Arrange Tiagos in LINE formation")
    time.sleep(1.0)
    
    test_endpoint("POST", "/supervisor/formation", {
        "formation_type": "triangle",
        "center_x": 0,
        "center_y": 0,
        "z": 0.095,
        "spacing": 2.0
    }, "Arrange Tiagos in TRIANGLE formation")
    time.sleep(1.0)
    
    test_endpoint("POST", "/supervisor/formation", {
        "formation_type": "circle",
        "center_x": 0,
        "center_y": 0,
        "z": 0.095,
        "spacing": 2.0
    }, "Arrange Tiagos in CIRCLE formation")
    time.sleep(1.0)
    
    # Test 6: Multi-Robot Commands
    print_section("6. MULTI-ROBOT COMMANDS")
    
    test_endpoint("POST", "/supervisor/multi_command", {
        "commands": [
            {"type": "teleport", "target": "mavic", "data": {"x": 0, "y": 0, "z": 3.0}},
            {"type": "teleport", "target": "tiago1", "data": {"x": -1, "y": 0, "z": 0.095}},
            {"type": "teleport", "target": "tiago2", "data": {"x": 0, "y": 0, "z": 0.095}},
            {"type": "teleport", "target": "tiago3", "data": {"x": 1, "y": 0, "z": 0.095}}
        ]
    }, "Execute multiple teleport commands")
    time.sleep(1.0)
    
    # Test 7: Mavic-Specific Commands
    print_section("7. MAVIC-SPECIFIC COMMANDS")
    
    test_endpoint("POST", "/supervisor/mavic/takeoff?altitude=2.5", None, "Mavic takeoff to 2.5m")
    time.sleep(0.5)
    
    test_endpoint("POST", "/supervisor/mavic/hover", None, "Mavic hover")
    time.sleep(0.5)
    
    test_endpoint("POST", "/supervisor/mavic/land", None, "Mavic land")
    time.sleep(0.5)
    
    # Test 8: Tiago-Specific Commands
    print_section("8. TIAGO-SPECIFIC COMMANDS")
    
    test_endpoint("POST", "/supervisor/tiago/1/move_to?x=2.0&y=1.0", None, "Tiago 1 move to (2, 1)")
    time.sleep(0.5)
    
    test_endpoint("POST", "/supervisor/tiago/1/forward?speed=0.5", None, "Tiago 1 move forward at 0.5 m/s")
    time.sleep(0.5)
    
    test_endpoint("POST", "/supervisor/tiago/2/rotate?angular_speed=0.5", None, "Tiago 2 rotate at 0.5 rad/s")
    time.sleep(0.5)
    
    # Test 9: Status & Monitoring
    print_section("9. STATUS & MONITORING")
    
    test_endpoint("GET", "/supervisor/position/mavic", None, "Get Mavic position")
    time.sleep(0.5)
    
    test_endpoint("GET", "/supervisor/status", None, "Get all robot status")
    time.sleep(0.5)
    
    test_endpoint("GET", "/supervisor/command", None, "Poll supervisor command")
    time.sleep(0.5)
    
    # Test 10: Command Management
    print_section("10. COMMAND MANAGEMENT")
    
    test_endpoint("DELETE", "/supervisor/command", None, "Clear command")
    time.sleep(0.5)
    
    # Summary
    print_section("TEST SUMMARY")
    print("✅ All supervisor endpoints tested!")
    print("\n📝 Next steps:")
    print("   1. Ensure Webots simulation is running")
    print("   2. Check Webots console for supervisor logs")
    print("   3. Verify robots are moving as commanded")
    print("   4. Check API docs at http://127.0.0.1:8000/docs")
    print()


if __name__ == "__main__":
    main()
