"""Quick test for Mavic takeoff and land commands."""

import requests
import time

API_URL = "http://127.0.0.1:8000"

def test_mavic_actions():
    print("🧪 Testing Mavic Takeoff and Land Commands\n")
    
    # Test 1: Takeoff
    print("1️⃣ Testing TAKEOFF...")
    resp = requests.post(f"{API_URL}/mavic/takeoff")
    print(f"   Response: {resp.json()}")
    print(f"   ✅ Mavic should be taking off to 1.0m altitude")
    print(f"   Check Webots console for: '🚁 Taking off to 1.00m'\n")
    time.sleep(3)
    
    # Test 2: Hover
    print("2️⃣ Testing HOVER...")
    resp = requests.post(f"{API_URL}/mavic/hover")
    print(f"   Response: {resp.json()}")
    print(f"   ✅ Mavic should be hovering in place")
    print(f"   Check Webots console for: '🚁 Hovering at X.XXm'\n")
    time.sleep(2)
    
    # Test 3: Land
    print("3️⃣ Testing LAND...")
    resp = requests.post(f"{API_URL}/mavic/land")
    print(f"   Response: {resp.json()}")
    print(f"   ✅ Mavic should be landing (descending to 0.1m)")
    print(f"   Check Webots console for: '🛬 Landing - target altitude: 0.10m'\n")
    time.sleep(3)
    
    # Test 4: Status check
    print("4️⃣ Checking STATUS...")
    resp = requests.get(f"{API_URL}/mavic/status")
    print(f"   Response: {resp.json()}")
    print(f"\n✅ Test complete!")
    print(f"\n📝 Expected behavior:")
    print(f"   - Drone should takeoff, hover, then land in Webots")
    print(f"   - Check Webots console for action logs")
    print(f"   - Altitude should change: 0 → 1.0 → 0.1")

if __name__ == "__main__":
    try:
        test_mavic_actions()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API at http://127.0.0.1:8000")
        print("   Make sure the backend is running!")
    except Exception as e:
        print(f"❌ Error: {e}")
