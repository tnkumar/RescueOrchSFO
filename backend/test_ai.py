import asyncio
import os
import sys
import logging

# Configure logging to see internal logs
logging.basicConfig(level=logging.INFO)

# Add current dir to path to find app module (assuming run from backend root)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.services.ai_coordinator import AIRescueCoordinator
except ImportError as e:
    print(f"Import Error: {e}")
    print("Make sure you run this script from the 'backend' directory!")
    sys.exit(1)

async def main():
    print("🚀 Testing AI Rescue Coordinator...")
    try:
        coord = AIRescueCoordinator()
        
        if not coord.ai_enabled:
            print("❌ AI NOT ENABLED (API Key missing or Init failed)")
            # Check why
            if not os.getenv("HACKATHON_GEMINI_API_KEY") and not os.getenv("GEMINI_API_KEY"):
                print("   Reason: Missing API Key in environment")
            return

        print(f"✅ AI Enabled. LLM Object: {coord.llm}")
        try:
             print(f"   Model Name: {coord.llm.model_name}")
        except:
             print("   (Model name attribute not found directly)")
        
        incidents = [
            {"id": "test_inc_1", "type": "fire", "severity": "critical", "location": {"x": 10, "y": 10, "z": 0}}
        ]
        
        print(f"\n🧠 Sending analysis request for {len(incidents)} incident(s)...")
        result = await coord.analyze_and_assign(incidents)
        
        print("\n📝 Result:")
        import json
        print(json.dumps(result, indent=2))
        
        if "error" in result:
             print("\n❌ AI Returned Error")
        else:
             print("\n✅ AI Analysis Success")

    except Exception as e:
        print(f"\n❌ CRASH DURING EXECUTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
