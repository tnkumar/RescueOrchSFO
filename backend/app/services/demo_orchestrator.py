
import asyncio
import logging
import json
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)

API_URL = "http://127.0.0.1:8000"
WORLD_FILE = "../worlds/rescue_orch.wbt"
ROBOT_NAME = "tiago1"

class DemoOrchestrator:
    def __init__(self):
        self._running = False
        self._task = None
        self.kitchen_coords = self._get_kitchen_location()

    def _result_parser(self, content, def_name):
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
            logger.error(f"Error parsing world file: {e}")
        return None

    def _get_kitchen_location(self):
        """Fetch Kitchen location (FIRE_VISUAL) from world file."""
        try:
            # Simple assumption: run from backend/app/..., so need to go up to root
            # Actually, CWD is usually where uvicorn runs.
            # Using absolute path structure or robust check
            import os
            # Try a few paths
            paths = [
                "../worlds/rescue_orch.wbt",
                "worlds/rescue_orch.wbt",
                "../../worlds/rescue_orch.wbt"
            ]
            
            content = ""
            for p in paths:
                if os.path.exists(p):
                    with open(p, 'r') as f:
                        content = f.read()
                    break
            
            if not content:
                logger.warning("World file not found for Demo Orchestrator. Using Fallback.")
                return {"x": 1.63, "y": 0.92, "z": 1.15}

            # We use FIRE_VISUAL as the text marker for the Kitchen incident
            coords = self._result_parser(content, "FIRE_VISUAL")
            if coords:
                logger.info(f"📂 Demo Orchestrator: Parsed Kitchen -> {coords}")
                return coords
            else:
                logger.warning("Could not find FIRE_VISUAL in world file. Using fallback.")
        except Exception as e:
            logger.error(f"World file read error: {e}")
            
        return {"x": 1.63, "y": 0.92, "z": 1.15}

    def start_demo(self):
        """Start the demo sequence task."""
        if self._running:
            logger.warning("Demo already running!")
            return
        
        self._running = True
        logger.info("🚀 STARTING AUTOMATED DEMO SEQUENCE")
        # Create background task
        self._task = asyncio.create_task(self._run_sequence())

    async def _fly_drone_to(self, client, target: dict):
        """
        Simulate flying drone to target by DIRECTLY teleporting to coordinates.
        This fixes the issue where drone would only change altitude.
        """
        logger.info(f"🚁 Flying drone towards {target}...")
        
        # User requested: [7.75, -1.45, 0.0] as base, with altitude 7.0m
        # We will use this as the target.
        # But we probably want to animate it a bit? No, user said "change the coordinates... in the simulation".
        # So we use teleport.
        
        target_x = 7.75
        target_y = -1.45
        target_z = 4.5 # High altitude
        
        # 1. Takeoff (Move Up)
        await client.post(f"{API_URL}/supervisor/teleport", json={
            "target": "mavic",
            "position": {"x": 0, "y": 0, "z": target_z}
        })
        await asyncio.sleep(2)
        
        # 2. Move to Location
        logger.info(f"🚁 Teleporting Drone to ({target_x}, {target_y}, {target_z})")
        
        # Explicit status update for UI (force sync)
        try:
            await client.post(f"{API_URL}/mission/robot/mavic/status", json={
                "status": "surveillance",
                "position": {"x": target_x, "y": target_y, "z": target_z},
                "step_completed": True
            })
            logger.info("✅ Forced Mavic UI update")
        except Exception as e:
            logger.error(f"Failed to force update Mavic: {e}")

        await client.post(f"{API_URL}/supervisor/teleport", json={
            "target": "mavic",
            "position": {"x": target_x, "y": target_y, "z": target_z}
        })
        await asyncio.sleep(2)
        
        # 3. Force Update Status so UI shows correct location
        # The supervisor updates ALL positions in its loop, so UI *should* see it.
        # But to be instant, we can try to report it or just log.
        # The user seems to say "set the position... instead of Position: (0.00, 0.00)".
        # This implies the UI was showing 0,0.
        # Reason: `mavic.py` reported 0,0.
        # NOW that we use supervisor, supervisor will report real position to `mission.py`.
        # AND frontend uses `mission.py`.
        # So it should be automatic!
        # BUT, `mavic` status is special.
        # Let's add a log to confirm.
        
        logger.info(f"🚁 Drone Arrived at Target Location: {target_x}, {target_y}, {target_z}")

    async def _run_sequence(self):
        """Main Demo Sequence."""
        try:
            async with httpx.AsyncClient() as client:
                
                # 1. Fly to Kitchen
                await self._fly_drone_to(client, self.kitchen_coords)
                
                # 2. Report Fire Incident
                logger.info("🔥 Reporting FIRE Incident...")
                incident = {
                    "type": "fire",
                    "location": self.kitchen_coords,
                    "severity": "critical",
                    "description": "Visual confirmation: Fire in Kitchen by Drone"
                }
                res = await client.post(f"{API_URL}/mission/incident/report", json=incident)
                if res.status_code != 200:
                    logger.error("Failed to report incident")
                    return
                
                logger.info("🤖 Incident Reported. Waiting for AI Assignment...")
                
                # 3. Wait for Robot 1 Assignment
                assigned = False
                for _ in range(20):
                    res = await client.get(f"{API_URL}/mission/status")
                    if res.status_code == 200:
                        status = res.json()
                        robots = status.get("robots", {})
                        tiago1_data = robots.get(ROBOT_NAME, {})
                        task = tiago1_data.get("task", "")
                        if task and ("fire" in task.lower() or "kitchen" in task.lower()):
                            assigned = True
                            logger.info(f"🎯 AI Assigned {ROBOT_NAME} to: {task}")
                            break
                    await asyncio.sleep(1)
                
                if not assigned:
                    logger.warning("AI Assignment Timed Out.")
                
                # 4. Simulate Robot 1 Extinguish
                # Need dependencies for AI interaction
                from app.services.dependencies import get_ai_coordinator
                from langchain_core.messages import HumanMessage
                ai_coord = get_ai_coordinator()
                
                # Helper for smooth UI updates
                async def _animate_movement(entity_id, start_pos, end_pos, duration=3.0, steps=20):
                    """Smoothly updates UI position for demo effect"""
                    sx, sy = start_pos.get("x", 0), start_pos.get("y", 0)
                    ex, ey = end_pos.get("x", 0), end_pos.get("y", 0)
                    dx = (ex - sx) / steps
                    dy = (ey - sy) / steps
                    
                    for i in range(steps):
                        cx = sx + dx * (i + 1)
                        cy = sy + dy * (i + 1)
                        # Force update mission state
                        if entity_id in ai_coord.mission_state["robots"]:
                            ai_coord.mission_state["robots"][entity_id]["position"] = {"x": cx, "y": cy, "z": 0.095}
                            # Also keep task updated if set
                            # ai_coord.mission_state["robots"][entity_id]["status"] = "engaged"
                        await asyncio.sleep(duration / steps)

                # 4. Simulate Robot 1 Extinguish
                logger.info(f"🚚 Moving Robots to Kitchen...")
                
                # New Logic: Sequential Teleport for Tiago1, Tiago2, Tiago3 near Kitchen
                # Drone is at target_x, target_y.
                base_x, base_y = 7.75, -1.45 # Hardcode as requested

                # ANIMATE DRONE TELEPORT (Visual fix)
                logger.info("🚁 Animating Drone Movement manually...")
                asyncio.create_task(_animate_movement("mavic", {"x":0,"y":0}, {"x": base_x, "y": base_y}, duration=2.0))
                
                logger.info(f"🔥 Re-Reporting FIRE Incident at ({base_x}, {base_y})...")
                incident["location"] = {"x": base_x, "y": base_y, "z": 0.0}
                await client.post(f"{API_URL}/mission/incident/report", json=incident)

                # Robot 1: -1.5m X (Behind/In front depending on axis)
                targets = [
                    {"id": 1, "offset_x": -1.5, "offset_y": 0.0, "role": "extinguishing fire"},
                    {"id": 2, "offset_x": -1.5, "offset_y": 1.5, "role": "rescuing victim"},
                    {"id": 3, "offset_x": -1.5, "offset_y": -1.5, "role": "clearing debris"}
                ]
                
                for t in targets:
                    rid = t["id"]
                    robot_name = f"tiago{rid}"
                    tx = base_x + t["offset_x"]
                    ty = base_y + t["offset_y"]
                    role_desc = t["role"]
                    
                    # Determine Status Color
                    status_type = "executing"
                    if "fire" in role_desc.lower() or "extinguish" in role_desc.lower():
                        status_type = "extinguishing"
                    elif "surveillance" in role_desc.lower():
                        status_type = "surveillance"
                    
                    # 1. Generate LLM Notification
                    fallback_msg = f"⚠️ AI Offline: {robot_name} deploying to ({tx:.2f}, {ty:.2f}) for {role_desc}."
                    notification = fallback_msg
                    
                    if ai_coord.ai_enabled and ai_coord.llm:
                        try:
                            # Use LLM to generate nice message
                            prompt = f"""
                            Generate a short, tactical status update for a robot named {robot_name}.
                            Action: Deploying to coordinates ({tx:.2f}, {ty:.2f}).
                            Mission: {role_desc}.
                            Style: Professional, concise, military/rescue style. Max 1 sentence.
                            """
                            resp = await ai_coord.llm.ainvoke([HumanMessage(content=prompt)])
                            if resp.content:
                                notification = resp.content.strip()
                        except Exception as e:
                            logger.error(f"LLM Generation failed: {e}")
                    
                    # 2. Assign Task & Notify
                    ai_coord.mission_state["robots"][robot_name]["task"] = notification
                    ai_coord.mission_state["robots"][robot_name]["status"] = status_type
                    
                    # Force UI update for Assignment
                    await client.post(f"{API_URL}/mission/robot/{robot_name}/status", json={
                        "status": status_type,
                        "task": notification,
                        "position": {"x": 0.0, "y": 0.0, "z": 0.095}, # Start pos
                        "step_completed": False
                    })

                    logger.info(f"📍 Deploying {robot_name} to ({tx:.2f}, {ty:.2f})...")
                    try:
                        # 3. Simulate Travel (5 seconds)
                        steps = 20
                        start_x, start_y = 0.0, 0.0
                        dx, dy = (tx - start_x) / steps, (ty - start_y) / steps
                        
                        for s in range(steps):
                            curr_x = start_x + dx * (s + 1)
                            curr_y = start_y + dy * (s + 1)
                            
                            ai_coord.mission_state["robots"][robot_name]["position"] = {"x": curr_x, "y": curr_y, "z": 0.095}
                            ai_coord.mission_state["robots"][robot_name]["status"] = "executing"
                            ai_coord.mission_state["robots"][robot_name]["task"] = f"Deploying to ({tx:.2f}, {ty:.2f})..."
                            
                            # Force UI update
                            await client.post(f"{API_URL}/mission/robot/{robot_name}/status", json={
                                "status": "executing",
                                "task": f"Moving to target... {int((s+1)/steps*100)}%",
                                "position": {"x": curr_x, "y": curr_y, "z": 0.095},
                                "step_completed": False
                            })
                            await asyncio.sleep(0.25) # Smooth travel
                        
                        # 4. Work Phase (Intermediate Steps!)
                        work_msg = f"{status_type.upper()} in progress..."
                        ai_coord.mission_state["robots"][robot_name]["status"] = status_type
                        ai_coord.mission_state["robots"][robot_name]["task"] = work_msg
                        
                        logger.info(f"⚙️ {robot_name} {work_msg}")
                        await client.post(f"{API_URL}/mission/robot/{robot_name}/status", json={
                            "status": status_type,
                            "task": work_msg,
                            "position": {"x": tx, "y": ty, "z": 0.095},
                            "step_completed": True # Mark arrival complete
                        })
                        
                        # Simulate work duration
                        for w in range(5):
                            await asyncio.sleep(1)
                            # Pulse status
                            await client.post(f"{API_URL}/mission/robot/{robot_name}/status", json={
                                "status": status_type,
                                "task": f"{work_msg} ({w+1}/5s)",
                                "position": {"x": tx, "y": ty, "z": 0.095}
                            })

                        # 5. Complete
                        logger.info(f"✅ {robot_name} Task Complete")
                        ai_coord.mission_state["robots"][robot_name]["status"] = "complete"
                        ai_coord.mission_state["robots"][robot_name]["task"] = "Mission Accomplished."
                        
                        await client.post(f"{API_URL}/mission/robot/{robot_name}/status", json={
                            "status": "complete",
                            "task": "Mission Accomplished.",
                            "position": {"x": tx, "y": ty, "z": 0.095},
                            "step_completed": True
                        })
                        
                    except Exception as e:
                        logger.error(f"❌ Failed to move {robot_name}: {e}")
                    
                    # Wait slightly before next robot
                    await asyncio.sleep(1.0)

                logger.info("✅ All Robots Deployed.")
                
                # FINAL LLM MESSAGE: Great Work
                final_msg = "Mission Accomplished: All units responded effectively."
                if ai_coord.ai_enabled and ai_coord.llm:
                    try:
                        prompt = "Generate a short, celebratory message for the rescue team saying 'Great work at rescuing people by responding on time'."
                        response = await ai_coord.llm.ainvoke([HumanMessage(content=prompt)])
                        final_msg = response.content.strip()
                    except: pass
                
                # Show Final Message on ALL robots
                for r in ["tiago1", "tiago2", "tiago3"]:
                    if r in ai_coord.mission_state["robots"]:
                         ai_coord.mission_state["robots"][r]["task"] = final_msg
                         ai_coord.mission_state["robots"][r]["status"] = "mission_complete"

                await asyncio.sleep(2)
                
                logger.info("🎬 Demo Sequence Complete.")
                
                # 5. Report Cleanup Incident (Trigger Robot 2)
                logger.info("🧹 Reporting 'Cleanup' Incident...")
                cleanup_incident = {
                    "type": "cleanup",
                    "location": {"x": base_x, "y": base_y, "z": 0.0},
                    "severity": "medium",
                    "description": "Fire extinguished. Debris removal required."
                }
                await client.post(f"{API_URL}/mission/incident/report", json=cleanup_incident)
                
                logger.info("✅ Demo Sequence Complete.")

                
        except Exception as e:
            logger.error(f"Demo Sequence Failed: {e}")
        finally:
            self._running = False

# Global Instance
demo_orchestrator = DemoOrchestrator()
