"""Test script to verify API commands are being sent and received correctly."""

import requests
import time

API_BASE = "http://localhost:8000"

def test_mavic():
    print("\n=== Testing Mavic Drone ===\n")
    
    # Test 1: Get status
    print("1. Getting Mavic status...")
    response = requests.get(f"{API_BASE}/mavic/status")
    print(f"   Status: {response.json()}")
    
    # Test 2: Takeoff
    print("\n2. Sending TAKEOFF command...")
    response = requests.post(f"{API_BASE}/mavic/takeoff")
    print(f"   Response: {response.json()}")
    time.sleep(1)
    
    # Test 3: Check command endpoint
    print("\n3. Checking what command is stored...")
    response = requests.get(f"{API_BASE}/mavic/command")
    print(f"   Stored command: {response.json()}")
    
    # Test 4: Send velocity
    print("\n4. Sending VELOCITY command (forward)...")
    response = requests.post(f"{API_BASE}/mavic/velocity", json={
        "pitch": -1.5,
        "roll": 0,
        "yaw": 0,
        "vertical": 0
    })
    print(f"   Response: {response.json()}")
    time.sleep(2)
    
    # Test 5: Land
    print("\n5. Sending LAND command...")
    response = requests.post(f"{API_BASE}/mavic/land")
    print(f"   Response: {response.json()}")


def test_tiago():
    print("\n=== Testing Tiago Robot #1 ===\n")
    
    # Test 1: Get status
    print("1. Getting Tiago status...")
    response = requests.get(f"{API_BASE}/tiago/1/status")
    print(f"   Status: {response.json()}")
    
    # Test 2: Send velocity
    print("\n2. Sending VELOCITY command (forward)...")
    response = requests.post(f"{API_BASE}/tiago/1/velocity", json={
        "linear_x": 0.5,
        "linear_y": 0,
        "angular": 0
    })
    print(f"   Response: {response.json()}")
    time.sleep(2)
    
    # Test 3: Check command endpoint
    print("\n3. Checking what command is stored...")
    response = requests.get(f"{API_BASE}/tiago/1/command")
    print(f"   Stored command: {response.json()}")
    
    # Test 4: Stop
    print("\n4. Sending STOP command...")
    response = requests.post(f"{API_BASE}/tiago/1/stop")
    print(f"   Response: {response.json()}")
    time.sleep(1)
    
    # Test 5: Head movement
    print("\n5. Sending HEAD command...")
    response = requests.post(f"{API_BASE}/tiago/1/head", json={
        "head_1": 0.5,
        "head_2": 0.3
    })
    print(f"   Response: {response.json()}")
    time.sleep(1)
    
    # Test 6: Torso lift
    print("\n6. Sending TORSO command...")
    response = requests.post(f"{API_BASE}/tiago/1/torso", json={
        "height": 0.2
    })
    print(f"   Response: {response.json()}")


if __name__ == "__main__":
    print("=" * 60)
    print("RescueOrchSFO API Test Script")
    print("=" * 60)
    print("\nThis script will send commands to the API.")
    print("Watch the Webots console for debug logs showing command execution.")
    print("\nMake sure:")
    print("  1. Backend is running (./run.bat)")
    print("  2. Webots simulation is running and in PLAY mode")
    print("  3. You can see the Webots console output")
    print("\n" + "=" * 60)
    
    input("\nPress ENTER to start testing...")
    
    try:
        test_mavic()
        test_tiago()
        
        print("\n" + "=" * 60)
        print("✅ All API commands sent successfully!")
        print("\nNow check the Webots console. You should see:")
        print("  - [mavic_api] ⚡ ACTION command: takeoff")
        print("  - [mavic_api] 🚁 VELOCITY command: pitch=-1.50...")
        print("  - [tiago_api_1] 🚀 VELOCITY command: linear_x=0.50...")
        print("  - [tiago_api_1] 👀 HEAD command: pan=0.50...")
        print("  - [tiago_api_1] ⬆️ TORSO command: height=0.20m")
        print("\nIf you DON'T see these logs, the controllers aren't polling the API.")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to backend!")
        print("Make sure the backend is running on http://localhost:8000")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
