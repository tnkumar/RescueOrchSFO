"""Quick automated endpoint test - no user interaction required."""

import requests
import time

API_BASE = "http://localhost:8000"

def test_all():
    print("Testing all API endpoints...")
    print("=" * 60)
    
    results = {
        "mavic": [],
        "tiago": [],
        "errors": []
    }
    
    # Test Mavic endpoints
    tests = [
        ("GET", "/mavic/status", None, "Mavic Status"),
        ("POST", "/mavic/takeoff", None, "Mavic Takeoff"),
        ("POST", "/mavic/velocity", {"pitch": -1.0, "roll": 0, "yaw": 0, "vertical": 0}, "Mavic Velocity"),
        ("POST", "/mavic/hover", None, "Mavic Hover"),
        ("POST", "/mavic/land", None, "Mavic Land"),
        ("GET", "/mavic/command", None, "Mavic Command Poll"),
    ]
    
    for method, endpoint, data, name in tests:
        try:
            url = f"{API_BASE}{endpoint}"
            if method == "GET":
                r = requests.get(url, timeout=2)
            else:
                r = requests.post(url, json=data, timeout=2)
            
            if r.status_code == 200:
                results["mavic"].append(f"✓ {name}")
            else:
                results["errors"].append(f"✗ {name} (status {r.status_code})")
        except Exception as e:
            results["errors"].append(f"✗ {name} ({str(e)[:50]})")
        time.sleep(0.5)
    
    # Test Tiago endpoints
    tests = [
        ("GET", "/tiago/1/status", None, "Tiago Status"),
        ("POST", "/tiago/1/velocity", {"linear_x": 0.5, "linear_y": 0, "angular": 0}, "Tiago Velocity"),
        ("POST", "/tiago/1/head", {"head_1": 0.5, "head_2": 0.3}, "Tiago Head"),
        ("POST", "/tiago/1/torso", {"height": 0.2}, "Tiago Torso"),
        ("POST", "/tiago/1/arm", {"arm": "right", "joint_positions": [0.2, -0.5, 0, 0.8, 0, 0, 0]}, "Tiago Arm"),
        ("POST", "/tiago/1/gripper", {"arm": "right", "action": "open"}, "Tiago Gripper"),
        ("POST", "/tiago/1/stop", None, "Tiago Stop"),
        ("GET", "/tiago/1/command", None, "Tiago Command Poll"),
    ]
    
    for method, endpoint, data, name in tests:
        try:
            url = f"{API_BASE}{endpoint}"
            if method == "GET":
                r = requests.get(url, timeout=2)
            else:
                r = requests.post(url, json=data, timeout=2)
            
            if r.status_code == 200:
                results["tiago"].append(f"✓ {name}")
            else:
                results["errors"].append(f"✗ {name} (status {r.status_code})")
        except Exception as e:
            results["errors"].append(f"✗ {name} ({str(e)[:50]})")
        time.sleep(0.5)
    
    # Print results
    print("\nMavic Endpoints:")
    for r in results["mavic"]:
        print(f"  {r}")
    
    print("\nTiago Endpoints:")
    for r in results["tiago"]:
        print(f"  {r}")
    
    if results["errors"]:
        print("\nErrors:")
        for e in results["errors"]:
            print(f"  {e}")
    
    print("\n" + "=" * 60)
    total_success = len(results["mavic"]) + len(results["tiago"])
    total_errors = len(results["errors"])
    print(f"Results: {total_success} passed, {total_errors} failed")
    
    if total_errors == 0:
        print("\n✅ ALL API ENDPOINTS WORKING!")
        print("\nNow check:")
        print("  1. Backend console - should show 📥 command logs")
        print("  2. Webots console - should show [mavic_api] and [tiago_api_1] logs")
        print("  3. Webots simulation - robots should have moved!")
    else:
        print("\n❌ Some endpoints failed - check backend is running")
    
    return total_errors == 0

if __name__ == "__main__":
    try:
        success = test_all()
        exit(0 if success else 1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend at http://localhost:8000")
        print("Make sure ./run.bat is running!")
        exit(1)
