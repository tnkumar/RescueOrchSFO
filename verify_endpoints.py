"""Comprehensive API endpoint verification script."""

import requests
import time
import sys

API_BASE = "http://localhost:8000"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

def print_test(name, status, details=""):
    symbol = f"{Colors.GREEN}✓{Colors.RESET}" if status else f"{Colors.RED}✗{Colors.RESET}"
    print(f"{symbol} {name}")
    if details:
        print(f"  {Colors.BLUE}→{Colors.RESET} {details}")

def test_endpoint(method, endpoint, data=None, expected_status=200):
    """Test an API endpoint and return success status."""
    try:
        url = f"{API_BASE}{endpoint}"
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        success = response.status_code == expected_status
        return success, response.json() if success else None
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 70)
    print(f"{Colors.BLUE}RescueOrchSFO - Complete API Endpoint Verification{Colors.RESET}")
    print("=" * 70)
    print("\nThis script tests ALL API endpoints and verifies Webots integration.")
    print(f"{Colors.YELLOW}IMPORTANT:{Colors.RESET} Watch the Webots console for command execution logs!")
    print("\nMake sure:")
    print("  1. Backend is running (./run.bat)")
    print("  2. Webots simulation is RUNNING and in PLAY mode")
    print("  3. You can see both backend console AND Webots console")
    print("=" * 70)
    
    input("\nPress ENTER to start testing...")
    
    # Test backend health
    print(f"\n{Colors.YELLOW}=== Backend Health Check ==={Colors.RESET}")
    success, data = test_endpoint("GET", "/health")
    print_test("Backend Health", success, f"Status: {data.get('status') if data else 'ERROR'}")
    
    if not success:
        print(f"\n{Colors.RED}❌ Backend is not running! Start it with ./run.bat{Colors.RESET}")
        sys.exit(1)
    
    # MAVIC TESTS
    print(f"\n{Colors.YELLOW}=== Mavic Drone Endpoints ==={Colors.RESET}")
    
    # 1. Status
    success, data = test_endpoint("GET", "/mavic/status")
    print_test("GET /mavic/status", success, f"Connected: {data.get('connected') if data else 'N/A'}")
    
    # 2. Takeoff
    print(f"\n{Colors.BLUE}Testing Mavic Takeoff...{Colors.RESET}")
    success, data = test_endpoint("POST", "/mavic/takeoff")
    print_test("POST /mavic/takeoff", success, f"Flying: {data.get('flying') if data else 'N/A'}")
    if success:
        print(f"  {Colors.YELLOW}→ Check Webots: Drone should take off!{Colors.RESET}")
    time.sleep(2)
    
    # 3. Velocity (Forward)
    print(f"\n{Colors.BLUE}Testing Mavic Velocity (Forward)...{Colors.RESET}")
    success, data = test_endpoint("POST", "/mavic/velocity", {
        "pitch": -1.5,
        "roll": 0,
        "yaw": 0,
        "vertical": 0
    })
    print_test("POST /mavic/velocity", success, "pitch=-1.5 (forward)")
    if success:
        print(f"  {Colors.YELLOW}→ Check Webots: Drone should move forward!{Colors.RESET}")
    time.sleep(3)
    
    # 4. Hover
    print(f"\n{Colors.BLUE}Testing Mavic Hover...{Colors.RESET}")
    success, data = test_endpoint("POST", "/mavic/hover")
    print_test("POST /mavic/hover", success)
    if success:
        print(f"  {Colors.YELLOW}→ Check Webots: Drone should hover in place!{Colors.RESET}")
    time.sleep(2)
    
    # 5. Altitude
    print(f"\n{Colors.BLUE}Testing Mavic Altitude Change...{Colors.RESET}")
    success, data = test_endpoint("POST", "/mavic/altitude", {"altitude": 2.0})
    print_test("POST /mavic/altitude", success, "Target: 2.0m")
    if success:
        print(f"  {Colors.YELLOW}→ Check Webots: Drone should climb to 2m!{Colors.RESET}")
    time.sleep(2)
    
    # 6. Land
    print(f"\n{Colors.BLUE}Testing Mavic Land...{Colors.RESET}")
    success, data = test_endpoint("POST", "/mavic/land")
    print_test("POST /mavic/land", success)
    if success:
        print(f"  {Colors.YELLOW}→ Check Webots: Drone should land!{Colors.RESET}")
    time.sleep(2)
    
    # 7. Command endpoint
    success, data = test_endpoint("GET", "/mavic/command")
    print_test("GET /mavic/command", success, f"Last command type: {data.get('type') if data else 'N/A'}")
    
    # TIAGO TESTS
    print(f"\n{Colors.YELLOW}=== Tiago Robot #1 Endpoints ==={Colors.RESET}")
    
    # 1. Status
    success, data = test_endpoint("GET", "/tiago/1/status")
    print_test("GET /tiago/1/status", success, f"Connected: {data.get('connected') if data else 'N/A'}")
    
    # 2. Velocity (Forward)
    print(f"\n{Colors.BLUE}Testing Tiago Velocity (Forward)...{Colors.RESET}")
    success, data = test_endpoint("POST", "/tiago/1/velocity", {
        "linear_x": 0.5,
        "linear_y": 0,
        "angular": 0
    })
    print_test("POST /tiago/1/velocity", success, "linear_x=0.5 (forward)")
    if success:
        print(f"  {Colors.YELLOW}→ Check Webots: Robot should move forward!{Colors.RESET}")
    time.sleep(3)
    
    # 3. Stop
    print(f"\n{Colors.BLUE}Testing Tiago Stop...{Colors.RESET}")
    success, data = test_endpoint("POST", "/tiago/1/stop")
    print_test("POST /tiago/1/stop", success)
    if success:
        print(f"  {Colors.YELLOW}→ Check Webots: Robot should stop!{Colors.RESET}")
    time.sleep(1)
    
    # 4. Head Movement
    print(f"\n{Colors.BLUE}Testing Tiago Head Movement...{Colors.RESET}")
    success, data = test_endpoint("POST", "/tiago/1/head", {
        "head_1": 0.5,
        "head_2": 0.3
    })
    print_test("POST /tiago/1/head", success, "pan=0.5, tilt=0.3")
    if success:
        print(f"  {Colors.YELLOW}→ Check Webots: Robot head should pan and tilt!{Colors.RESET}")
    time.sleep(2)
    
    # 5. Torso Lift
    print(f"\n{Colors.BLUE}Testing Tiago Torso Lift...{Colors.RESET}")
    success, data = test_endpoint("POST", "/tiago/1/torso", {
        "height": 0.2
    })
    print_test("POST /tiago/1/torso", success, "height=0.2m")
    if success:
        print(f"  {Colors.YELLOW}→ Check Webots: Robot torso should lift!{Colors.RESET}")
    time.sleep(2)
    
    # 6. Arm Movement
    print(f"\n{Colors.BLUE}Testing Tiago Arm Movement...{Colors.RESET}")
    success, data = test_endpoint("POST", "/tiago/1/arm", {
        "arm": "right",
        "joint_positions": [0.2, -0.5, 0.0, 0.8, 0.0, 0.0, 0.0]
    })
    print_test("POST /tiago/1/arm", success, "right arm with 7 joint positions")
    if success:
        print(f"  {Colors.YELLOW}→ Check Webots: Right arm should move!{Colors.RESET}")
    time.sleep(2)
    
    # 7. Gripper
    print(f"\n{Colors.BLUE}Testing Tiago Gripper...{Colors.RESET}")
    success, data = test_endpoint("POST", "/tiago/1/gripper", {
        "arm": "right",
        "action": "open"
    })
    print_test("POST /tiago/1/gripper", success, "right gripper → OPEN")
    if success:
        print(f"  {Colors.YELLOW}→ Check Webots: Right gripper should open!{Colors.RESET}")
    time.sleep(1)
    
    # 8. Home Arms Action
    print(f"\n{Colors.BLUE}Testing Tiago Home Arms...{Colors.RESET}")
    success, data = test_endpoint("POST", "/tiago/1/action", {
        "action": "home_arms"
    })
    print_test("POST /tiago/1/action (home_arms)", success)
    if success:
        print(f"  {Colors.YELLOW}→ Check Webots: Arms should return to home position!{Colors.RESET}")
    time.sleep(2)
    
    # 9. Command endpoint
    success, data = test_endpoint("GET", "/tiago/1/command")
    print_test("GET /tiago/1/command", success, f"Last command type: {data.get('type') if data else 'N/A'}")
    
    # Summary
    print("\n" + "=" * 70)
    print(f"{Colors.GREEN}✅ All API endpoints tested!{Colors.RESET}")
    print("\n" + "=" * 70)
    print(f"{Colors.YELLOW}VERIFICATION CHECKLIST:{Colors.RESET}")
    print("\nCheck your Webots console for these logs:")
    print("  [mavic_api] ⚡ ACTION command: takeoff")
    print("  [mavic_api] 🚁 VELOCITY command: pitch=-1.50...")
    print("  [mavic_api] 📏 Altitude change: 1.00m → 2.00m")
    print("  [tiago_api_1] 🚀 VELOCITY command: linear_x=0.50...")
    print("  [tiago_api_1] 👀 HEAD command: pan=0.50, tilt=0.30")
    print("  [tiago_api_1] ⬆️ TORSO command: height=0.20m")
    print("  [tiago_api_1] 🦾 ARM command: right arm → [...]")
    print("  [tiago_api_1] ✋ GRIPPER command: right → OPEN")
    print("\nCheck your backend console for these logs:")
    print("  📥 MAVIC TAKEOFF endpoint called")
    print("  📥 MAVIC VELOCITY command received: pitch=-1.50...")
    print("  📥 TIAGO-1 VELOCITY command received: linear_x=0.50...")
    print("  📥 TIAGO-1 HEAD command received: pan=0.50...")
    print("\n" + "=" * 70)
    print(f"{Colors.BLUE}If you see logs in BOTH consoles AND robots moved in Webots:{Colors.RESET}")
    print(f"  {Colors.GREEN}✅ System is working perfectly!{Colors.RESET}")
    print(f"\n{Colors.BLUE}If you see backend logs but NO Webots logs:{Colors.RESET}")
    print(f"  {Colors.RED}❌ Controllers aren't polling - restart Webots{Colors.RESET}")
    print(f"\n{Colors.BLUE}If you see both logs but robots DON'T move:{Colors.RESET}")
    print(f"  {Colors.RED}❌ Physics/simulation issue - check for warnings{Colors.RESET}")
    print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Test interrupted by user{Colors.RESET}")
    except requests.exceptions.ConnectionError:
        print(f"\n{Colors.RED}❌ ERROR: Cannot connect to backend at {API_BASE}{Colors.RESET}")
        print("Make sure the backend is running with ./run.bat")
    except Exception as e:
        print(f"\n{Colors.RED}❌ ERROR: {e}{Colors.RESET}")
