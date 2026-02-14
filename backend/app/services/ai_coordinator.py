"""AI Rescue Coordinator Service using basic Gemini API (simplified for demo)."""

import os
import json
import logging
from typing import List, Dict
from dotenv import load_dotenv

# Missing imports added here
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Known Locations for Semantic Resolution
KNOWN_LOCATIONS = {
    "Kitchen": {"x": 1.63, "y": 0.92, "z": 1.15},
    "Living Room": {"x": 0.0, "y": 0.0, "z": 0.0},
    "Entrance": {"x": 1.36, "y": -7.28, "z": 0.0},
}


class AIRescueCoordinator:
    """AI-powered rescue mission coordinator using LangChain + Gemini 1.5 Flash."""
    
    def __init__(self):
        """Initialize AI coordinator with LangChain."""
        # Check for API key
        api_key = os.getenv("HACKATHON_GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            logger.warning("⚠️ Gemini API key not found - AI analysis will use fallback logic")
            self.ai_enabled = False
            self.llm = None
        else:
            logger.info("✅ Gemini API key found - Initializing LangChain")
            self.ai_enabled = True
            try:
                # Initialize LangChain ChatGoogleGenerativeAI
                # User specifically requested 'gemini-2.5-flash'
                logger.info("🌟 Initializing Gemini 2.5 Flash (User Request)")
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    api_key=api_key,
                    temperature=0.2,
                    convert_system_message_to_human=True
                )
            except Exception as e:
                logger.error(f"❌ Failed to init Gemini 2.5 Flash: {e}")
                logger.info("⚠️ Attempting fallback to gemini-1.5-flash...")
                try:
                    self.llm = ChatGoogleGenerativeAI(
                        model="gemini-1.5-flash",
                        api_key=api_key,
                        temperature=0.2
                    )
                    logger.info("✅ Fallback to Gemini 1.5 Flash successful")
                except Exception as e2:
                    logger.error(f"❌ Fallback failed: {e2}")
                    self.ai_enabled = False
                    self.llm = None
        
        # Mission state
        self.mission_state = {
            "active": False,
            "incidents": [],
            "robots": {
                "mavic": {
                    "name": "Mavic 2 Pro",
                    "position": {"x": 0, "y": 0, "z": 0.1},
                    "status": "ready",
                    "type": "drone",
                    "task": None,
                    "current_step": 0
                },
                "tiago1": {
                    "name": "TIAGo++",
                    "position": {"x": 0.66, "y": 5.81, "z": 0.095},
                    "status": "ready",
                    "task": None,
                    "current_step": 0
                },
                "tiago2": {
                    "name": "TIAGo++(1)",
                    "position": {"x": 1.36, "y": -7.28, "z": 0.095},
                    "status": "ready",
                    "task": None,
                    "current_step": 0
                },
                "tiago3": {
                    "name": "TIAGo++(2)",
                    "position": {"x": 3.5, "y": 0, "z": 0.095},
                    "status": "ready",
                    "task": None,
                    "current_step": 0
                }
            },
            "assignments": {},
            "completed": []
        }
        
        logger.info("AI Rescue Coordinator initialized (LangChain Mode)")
    
    async def analyze_and_assign(self, incidents: List[Dict]) -> Dict:
        """
        AI analyzes incidents and creates rescue plan using LangChain.
        """
        if not incidents:
            return {"error": "No incidents to analyze"}
        
        logger.info("=" * 80)
        logger.info("🤖 AI RESCUE COORDINATOR - LANGCHAIN GEMINI ANALYSIS")
        logger.info("=" * 80)
        
        # Log incidents
        logger.info(f"\n📋 ANALYZING {len(incidents)} INCIDENT(S):")
        for i, incident in enumerate(incidents, 1):
            logger.info(f"  #{i}: {incident['type'].upper()} ({incident['severity']})")

        # 1. BUILD PROMPT AND MESSAGES
        available_robots = self.mission_state["robots"]
        
        system_prompt = "You are the AI Rescue Coordinator. detailed, precise, and efficient."
        
        user_prompt = f"""
Analyze these incidents and assign robots.

KNOWN LOCATIONS:
{json.dumps(KNOWN_LOCATIONS, indent=2)}

INCIDENTS:
{json.dumps(incidents, indent=2)}

AVAILABLE ROBOTS:
{json.dumps(available_robots, indent=2)}

INSTRUCTIONS:
1. Assign one robot to each incident based on proximity and capabilities.
2. If incident location is a name (e.g., "Kitchen"), usage KNOWN LOCATIONS to find coordinates.
3. Prioritize CRITICAL incidents.
4. Generate a 3-step action plan for each robot (Navigate -> Execute Task -> Report).
5. Return PURE JSON with this structure:
{{
  "analysis": "Brief summary of reasoning",
  "priority_ranking": [{{"incident_id": "...", "reason": "..."}}],
  "robot_assignments": [
    {{
      "robot_id": "...",
      "incident_id": "...",
      "role": "...",
      "action_plan": [
        {{"step": 1, "action": "navigate", "target": {{"x": 0, "y": 0, "z": 0}}, "description": "..."}},
        {{"step": 2, "action": "execute_task", "duration": 30, "description": "..."}},
        {{"step": 3, "action": "report_complete", "description": "..."}}
      ]
    }}
  ]
}}
"""
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        # 2. CALL GEMINI API VIA LANGCHAIN
        if self.ai_enabled and self.llm:
            try:
                logger.info("\n🧠 Sending request to LangChain/Gemini...")
                response = await self.llm.ainvoke(messages)
                ai_text = response.content
                
                # Cleanup markdown code blocks
                if "```json" in ai_text:
                    ai_text = ai_text.split("```json")[1].split("```")[0]
                elif "```" in ai_text:
                    ai_text = ai_text.split("```")[1].split("```")[0]
                
                result = json.loads(ai_text)
                logger.info("✅ LangChain Analysis Successful")
                logger.info(f"💡 AI Reasoning: {result.get('analysis')}")
                
            except Exception as e:
                logger.error(f"❌ LangChain API Failed: {e}")
                logger.info("⚠️ Falling back to simple logic")
                return self._fallback_logic(incidents)
        else:
            logger.warning("⚠️ AI disabled - using fallback logic")
            return self._fallback_logic(incidents)

        # 3. APPLY ASSIGNMENTS
        robot_assignments = result.get("robot_assignments", [])
        
        logger.info("\n📊 MISSION ASSIGNMENTS (AI GENERATED):")
        for assignment in robot_assignments:
            robot_id = assignment["robot_id"]
            if robot_id in self.mission_state["robots"]:
                self.mission_state["assignments"][robot_id] = {
                    **assignment,
                    "current_step": 0,
                    "status": "assigned"
                }
                self.mission_state["robots"][robot_id]["task"] = assignment["incident_id"]
                self.mission_state["robots"][robot_id]["status"] = "assigned"
                
                logger.info(f"\n  ✅ {robot_id.upper()}:")
                logger.info(f"     Task: {assignment['role']}")
                logger.info(f"     Plan: {len(assignment['action_plan'])} steps")
        
        return result

    async def analyze_image(self, image_bytes: bytes, filename: str = "image.jpg") -> Dict:
        """
        Analyze an image using the vision model.
        """
        if not self.ai_enabled or not self.llm:
            return {"error": "AI not enabled"}
            
        try:
            import base64
            image_base64 = base64.b64encode(image_bytes).decode()
            
            prompt = """
            Analyze this image from a rescue drone and return JSON with:
            - objects_detected: list of strings
            - scene_description: string
            - safety_issues: list of strings
            - key_insights: string
            """
            
            msg = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{image_base64}",
                    },
                ]
            )
            
            logger.info(f"🧠 Analyzing image: {filename}...")
            response = await self.llm.ainvoke([msg])
            analysis_text = response.content
            
            # Try to parse JSON if possible, otherwise return text
            try:
                if "```json" in analysis_text:
                    json_str = analysis_text.split("```json")[1].split("```")[0]
                    return json.loads(json_str)
                elif "```" in analysis_text:
                    json_str = analysis_text.split("```")[1].split("```")[0]
                    return json.loads(json_str)
            except:
                pass
                
            return {"analysis": analysis_text}
            
        except Exception as e:
            logger.error(f"❌ Image Analysis Failed: {e}")
            return {"error": str(e)}

    def _fallback_logic(self, incidents: List[Dict]) -> Dict:
        """Backup logic if AI fails."""
        # Simple rule-based assignment for demo
        robot_assignments = []
        available_robots = ["tiago1", "tiago2", "tiago3"]
        
        for i, incident in enumerate(incidents):
            if i >= len(available_robots): break
            
            robot_id = available_robots[i]
            incident_loc = incident.get("location", {})
            
            assignment = {
                "robot_id": robot_id,
                "incident_id": incident.get("id", f"incident_{i+1}"),
                "role": f"{incident['type']} response (Fallback)",
                "action_plan": [
                    {
                        "step": 1,
                        "action": "navigate",
                        "target": {"x": incident_loc.get("x", 0), "y": incident_loc.get("y", 0), "z": 0.095},
                        "description": f"Navigate to {incident['type']}"
                    },
                    {
                        "step": 2,
                        "action": "execute_task",
                        "duration": 30,
                        "description": "Handle incident"
                    },
                    {
                        "step": 3,
                        "action": "report_complete",
                        "description": "Report complete"
                    }
                ]
            }
            robot_assignments.append(assignment)
            
            # Store assignments
            self.mission_state["assignments"][robot_id] = {
                **assignment,
                "current_step": 0,
                "status": "assigned"
            }
            self.mission_state["robots"][robot_id]["task"] = assignment["incident_id"]
            self.mission_state["robots"][robot_id]["status"] = "assigned"
            
        return {
            "analysis": "Fallback logic used (AI unavailable)",
            "robot_assignments": robot_assignments
        }
    
    def get_next_action(self, robot_id: str) -> Dict:
        """Get next action for a robot based on current progress."""
        assignment = self.mission_state["assignments"].get(robot_id)
        if not assignment:
            return {
                "action": "standby",
                "message": "No task assigned",
                "robot_id": robot_id
            }
        
        current_step = assignment.get("current_step", 0)
        action_plan = assignment.get("action_plan", [])
        
        if current_step >= len(action_plan):
            return {
                "action": "task_complete",
                "message": "All steps completed",
                "robot_id": robot_id
            }
        
        next_action = action_plan[current_step]
        # logger.info(f"{robot_id}: Next action - Step {next_action['step']}: {next_action['action']}")
        
        return {
            **next_action,
            "robot_id": robot_id,
            "total_steps": len(action_plan)
        }
    
    def update_robot_status(self, robot_id: str, status: Dict) -> Dict:
        """Update robot status and progress."""
        if robot_id not in self.mission_state["robots"]:
            return {"error": f"Unknown robot: {robot_id}"}
        
        # Update robot state
        self.mission_state["robots"][robot_id].update(status)
        
        # If step completed, advance to next step
        if status.get("step_completed"):
            assignment = self.mission_state["assignments"].get(robot_id)
            if assignment:
                assignment["current_step"] += 1
                logger.info(f"{robot_id}: Completed step {assignment['current_step']}")
        
        # Get next action
        next_action = self.get_next_action(robot_id)
        
        return {
            "status": "updated",
            "robot_id": robot_id,
            "next_action": next_action
        }
