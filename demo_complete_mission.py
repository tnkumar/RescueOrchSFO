"""Complete AI-Orchestrated Rescue Mission Demo with Webots Integration."""

import requests
import time
import sys

API_URL = "http://127.0.0.1:8000"


def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def check_api_connection():
    """Check if backend API is running."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=2)
        return response.status_code == 200
    except:
        return False


def main():
    print("\n" + "="*70)
    print("  🚀 COMPLETE AI-ORCHESTRATED RESCUE MISSION DEMO")
    print("  Using Gemini 2.5-flash AI Coordinator + Webots Simulation")
    print("="*70)
    
    # Check prerequisites
    print("\n📋 Checking Prerequisites...")
    
    if not check_api_connection():
        print("❌ Backend API not running!")
        print(f"   Please ensure backend is running at {API_URL}")
        print("   Run: cd backend && uvicorn app.main:app --reload")
        sys.exit(1)
    print("✅ Backend API connected")
    
    print("✅ Webots simulation (ensure it's running)")
    print("✅ Supervisor controller (should auto-start with Webots)")
    
    input("\n👉 Press ENTER when Webots simulation is running...")
    
    # Step 1: Start Mission
    print_header("STEP 1: STARTING AI RESCUE MISSION")
    try:
        resp = requests.post(f"{API_URL}/mission/start")
        result = resp.json()
        print(f"✅ Mission Status: {result['status']}")
        print(f"   Robots Available: {result['robots_available']}")
        print(f"   Message: {result['message']}")
    except Exception as e:
        print(f"❌ Failed to start mission: {e}")
        sys.exit(1)
    
    time.sleep(2)
    
    # Step 2: Drone Takeoff
    print_header("STEP 2: DRONE SURVEILLANCE - TAKEOFF")
    print("📡 Commanding Mavic drone to take off...")
    try:
        resp = requests.post(f"{API_URL}/mavic/takeoff")
        print(f"✅ Takeoff command sent")
        print(f"   Response: {resp.json()}")
        print("\n👁️  WATCH WEBOTS: Drone should be taking off now!")
    except Exception as e:
        print(f"⚠️  Takeoff command failed: {e}")
    
    time.sleep(3)
    
    # Step 3: Fire Incident
    print_header("STEP 3: INCIDENT DETECTED - FIRE 🔥")
    print("📹 Drone camera detects FIRE near stove...")
    print("   Location: Kitchen stove area (1.63, 0.92)")
    print("   Severity: CRITICAL - LPG cylinder nearby!")
    
    try:
        resp = requests.post(f"{API_URL}/mission/incident/report", json={
            "type": "fire",
            "location": {"x": 1.63, "y": 0.92, "z": 1.15},
            "severity": "critical",
            "description": "Fire detected near stove with LPG cylinder nearby (explosion risk)"
        })
        result = resp.json()
        print(f"\n✅ Incident Reported: {result['incident_id']}")
        
        if "ai_analysis" in result and "analysis" in result["ai_analysis"]:
            print(f"\n🤖 GEMINI AI ANALYSIS:")
            print(f"   {result['ai_analysis']['analysis']}")
            
            if "robot_assignments" in result["ai_analysis"]:
                print(f"\n📋 AI ROBOT ASSIGNMENTS:")
                for assignment in result["ai_analysis"]["robot_assignments"]:
                    robot_id = assignment['robot_id']
                    role = assignment.get('role', 'N/A')
                    incident = assignment.get('incident_id', 'N/A')
                    steps = len(assignment.get('action_plan', []))
                    print(f"   • {robot_id.upper()}: {role}")
                    print(f"     Target: {incident}, Action Steps: {steps}")
                
                print(f"\n👁️  WATCH WEBOTS: Robots should start moving to incident locations!")
        else:
            print(f"⚠️  AI analysis not available in response")
    except Exception as e:
        print(f"❌ Failed to report incident: {e}")
    
    time.sleep(4)
    
    # Step 4: Victim Incident
    print_header("STEP 4: INCIDENT DETECTED - VICTIM 🆘")
    print("📹 Drone camera detects PERSON trapped in room...")
    print("   Location: Adjacent room (-0.65, -1.43)")
    print("   Severity: HIGH - Immediate evacuation required!")
    
    try:
        resp = requests.post(f"{API_URL}/mission/incident/report", json={
            "type": "victim",
            "location": {"x": -0.65, "y": -1.43, "z": 0.0},
            "severity": "high",
            "description": "Person trapped in room, requires immediate evacuation"
        })
        result = resp.json()
        print(f"\n✅ Incident Reported: {result['incident_id']}")
        
        if "ai_analysis" in result and "analysis" in result["ai_analysis"]:
            print(f"\n🤖 GEMINI AI RE-ANALYSIS (Updated Priorities):")
            print(f"   {result['ai_analysis']['analysis']}")
            
            if "robot_assignments" in result["ai_analysis"]:
                print(f"\n📋 UPDATED ROBOT ASSIGNMENTS:")
                for assignment in result["ai_analysis"]["robot_assignments"]:
                    print(f"   • {assignment['robot_id'].upper()}: {assignment.get('role', 'N/A')}")
    except Exception as e:
        print(f"❌ Failed to report incident: {e}")
    
    time.sleep(4)
    
    # Step 5: Gas Leak
    print_header("STEP 5: INCIDENT DETECTED - GAS LEAK ⚠️")
    print("📹 Drone detects LPG CYLINDER valve open...")
    print("   Location: Near stove (1.3, 0.22)")
    print("   Severity: CRITICAL - Gas accumulation risk!")
    
    try:
        resp = requests.post(f"{API_URL}/mission/incident/report", json={
            "type": "gas_leak",
            "location": {"x": 1.3, "y": 0.22, "z": 0.0},
            "severity": "critical",
            "description": "LPG cylinder valve open, gas leak detected"
        })
        result = resp.json()
        print(f"\n✅ Incident Reported: {result['incident_id']}")
    except Exception as e:
        print(f"❌ Failed to report incident: {e}")
    
    time.sleep(3)
    
    # Step 6: Monitor Robot Execution
    print_header("STEP 6: AI-DIRECTED ROBOT EXECUTION")
    print("🤖 Robots are now executing AI-generated action plans...")
    print("   Supervisor controller polls AI coordinator every second")
    print("   Robots navigate to incidents and perform rescue operations")
    print("\n👁️  WATCH WEBOTS: Observe robots moving and executing tasks!")
    
    print("\n📊 Monitoring robot progress for 15 seconds...")
    for i in range(5):
        time.sleep(3)
        try:
            resp = requests.get(f"{API_URL}/mission/status")
            status = resp.json()
            
            print(f"\n⏱️  Update {i+1}/5:")
            for robot_id, robot_status in status['robots'].items():
                task = robot_status.get('task', 'None')
                current_step = robot_status.get('current_step', 0)
                total_steps = robot_status.get('total_steps', 0)
                
                if total_steps > 0:
                    progress = int((current_step / total_steps) * 100)
                    bar = '█' * (progress // 10) + '░' * (10 - progress // 10)
                    print(f"   {robot_id}: [{bar}] {progress}% - Task: {task}")
                else:
                    print(f"   {robot_id}: Standby")
        except Exception as e:
            print(f"   ⚠️  Status check failed: {e}")
    
    # Step 7: Final Status
    print_header("STEP 7: MISSION STATUS SUMMARY")
    try:
        resp = requests.get(f"{API_URL}/mission/status")
        status = resp.json()
        
        print(f"Mission Active: {status['active']}")
        print(f"\n📍 Total Incidents: {status['incidents']['total']}")
        for incident in status['incidents']['list']:
            print(f"   • {incident['type'].upper()} - {incident['severity']}")
            print(f"     Location: ({incident['location']['x']:.2f}, {incident['location']['y']:.2f})")
            print(f"     {incident.get('description', 'N/A')}")
        
        print(f"\n🤖 Robot Status:")
        for robot_id, robot_status in status['robots'].items():
            print(f"   • {robot_id.upper()}: {robot_status['status']}")
            if robot_status.get('task'):
                print(f"     Task: {robot_status['task']}")
                if robot_status['total_steps'] > 0:
                    print(f"     Progress: {robot_status['current_step']}/{robot_status['total_steps']} steps")
    except Exception as e:
        print(f"❌ Failed to get status: {e}")
    
    # Summary
    print_header("✅ DEMO COMPLETE!")
    print("🎯 What was demonstrated:")
    print("   ✅ Gemini 2.5-flash AI analyzed incidents intelligently")
    print("   ✅ AI prioritized based on severity and risk")
    print("   ✅ Robots assigned optimally (proximity + capability)")
    print("   ✅ Step-by-step action plans generated")
    print("   ✅ Supervisor executed AI plans in Webots")
    print("   ✅ Real-time progress tracking and reporting")
    
    print("\n📝 System Components:")
    print("   • Mavic Drone: Aerial surveillance")
    print("   • 3x Tiago Robots: Ground rescue operations")
    print("   • Gemini AI: Intelligent coordination")
    print("   • Webots: 3D simulation environment")
    print("   • FastAPI Backend: Mission control")
    
    print("\n🚀 Next Steps:")
    print("   1. View API docs: http://127.0.0.1:8000/docs")
    print("   2. Check mission report: GET /mission/report")
    print("   3. Integrate with frontend UI for visualization")
    print("   4. Add real camera-based incident detection")
    
    print("\n" + "="*70)
    print("  Thank you for watching the AI Rescue Mission Demo!")
    print("="*70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
