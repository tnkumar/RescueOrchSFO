"""Mission Control API for AI-orchestrated rescue operations."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import time
import logging

from app.services.ai_coordinator import AIRescueCoordinator
from app.services.dependencies import get_ai_coordinator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mission", tags=["Mission Control"])



class Incident(BaseModel):
    """Incident report model."""
    type: str = Field(..., description="Incident type: fire, victim, gas_leak, blocked_exit")
    location: dict = Field(..., description="Location coordinates {x, y, z}")
    severity: str = Field(..., description="Severity: critical, high, medium, low")
    description: Optional[str] = Field(None, description="Additional details")


class RobotStatus(BaseModel):
    """Robot status update model."""
    position: Optional[dict] = None
    status: Optional[str] = None
    step_completed: Optional[bool] = False
    message: Optional[str] = None


@router.post("/start")
async def start_mission():
    """
    Start a new rescue mission.
    Initializes AI coordinator and resets mission state.
    """
    ai_coordinator = get_ai_coordinator()
    
    ai_coordinator.mission_state["active"] = True
    ai_coordinator.mission_state["incidents"] = []
    ai_coordinator.mission_state["assignments"] = {}
    ai_coordinator.mission_state["completed"] = []
    
    # Reset robot states
    for robot_id in ai_coordinator.mission_state["robots"]:
        ai_coordinator.mission_state["robots"][robot_id].update({
            "status": "ready",
            "task": None,
            "current_step": 0
        })
    
    logger.info("🚀 Rescue mission started")
    
    # TRIGGER AUTOMATED DEMO SEQUENCE
    from app.services.demo_orchestrator import demo_orchestrator
    demo_orchestrator.start_demo()
    
    return {
        "status": "mission_started",
        "timestamp": time.time(),
        "robots_available": len(ai_coordinator.mission_state["robots"]),
        "message": "AI-orchestrated rescue mission initialized (DEMO MODE)"
    }


@router.post("/incident/report")
async def report_incident(incident: Incident):
    """
    Report a detected incident (typically from drone surveillance).
    Automatically triggers AI analysis and robot assignment.
    """
    ai_coordinator = get_ai_coordinator()
    
    if not ai_coordinator.mission_state["active"]:
        raise HTTPException(400, "Mission not active. Call /mission/start first.")
    
    # Create incident record
    incident_dict = incident.model_dump()
    incident_id = f"incident_{len(ai_coordinator.mission_state['incidents']) + 1}"
    incident_dict["id"] = incident_id
    incident_dict["timestamp"] = time.time()
    incident_dict["status"] = "detected"
    
    ai_coordinator.mission_state["incidents"].append(incident_dict)
    
    logger.info(f"📍 Incident reported: {incident.type} at ({incident.location['x']:.2f}, {incident.location['y']:.2f}) - {incident.severity}")
    
    # Trigger AI analysis
    logger.info("🤖 Triggering AI analysis...")
    analysis = await ai_coordinator.analyze_and_assign(ai_coordinator.mission_state["incidents"])
    
    if "error" in analysis:
        logger.error(f"AI analysis failed: {analysis['error']}")
        return {
            "status": "incident_reported",
            "incident_id": incident_id,
            "ai_analysis": analysis
        }
    
    logger.info(f"✅ AI analysis complete: {len(analysis.get('robot_assignments', []))} robots assigned")
    
    return {
        "status": "incident_reported",
        "incident_id": incident_id,
        "ai_analysis": analysis,
        "message": "Incident reported and AI analysis completed"
    }


@router.get("/incidents")
def get_incidents():
    """Get all detected incidents."""
    ai_coordinator = get_ai_coordinator()
    incidents = ai_coordinator.mission_state["incidents"]
    return {
        "incidents": incidents,
        "count": len(incidents),
        "active_mission": ai_coordinator.mission_state["active"]
    }


@router.post("/ai/analyze")
async def trigger_ai_analysis():
    """
    Manually trigger AI analysis of all incidents.
    Useful for re-analyzing after status changes.
    """
    ai_coordinator = get_ai_coordinator()
    
    if not ai_coordinator.mission_state["incidents"]:
        raise HTTPException(400, "No incidents to analyze")
    
    logger.info("🤖 Manual AI analysis triggered")
    analysis = await ai_coordinator.analyze_and_assign(ai_coordinator.mission_state["incidents"])
    
    return {
        "status": "analysis_complete",
        "analysis": analysis
    }


@router.get("/ai/plan/{robot_id}")
def get_robot_plan(robot_id: str):
    """
    Get AI-generated action plan for a specific robot.
    Used by supervisor to get next actions.
    """
    ai_coordinator = get_ai_coordinator()
    
    if robot_id not in ai_coordinator.mission_state["robots"]:
        raise HTTPException(404, f"Robot not found: {robot_id}")
    
    next_action = ai_coordinator.get_next_action(robot_id)
    assignment = ai_coordinator.mission_state["assignments"].get(robot_id)
    
    return {
        "robot_id": robot_id,
        "next_action": next_action,
        "full_assignment": assignment,
        "robot_status": ai_coordinator.mission_state["robots"][robot_id]
    }


@router.post("/robot/{robot_id}/status")
def update_robot_status(robot_id: str, status: RobotStatus):
    """
    Robot reports progress update.
    Returns next action from AI coordinator.
    """
    ai_coordinator = get_ai_coordinator()
    
    if robot_id not in ai_coordinator.mission_state["robots"]:
        raise HTTPException(404, f"Robot not found: {robot_id}")
    
    status_dict = status.model_dump(exclude_none=True)
    result = ai_coordinator.update_robot_status(robot_id, status_dict)
    
    logger.info(f"📊 {robot_id} status updated: {status_dict.get('message', 'progress update')}")
    
    return result


@router.get("/status")
def get_mission_status():
    """Get overall mission status and progress."""
    ai_coordinator = get_ai_coordinator()
    
    robots_status = {}
    for robot_id, robot_data in ai_coordinator.mission_state["robots"].items():
        assignment = ai_coordinator.mission_state["assignments"].get(robot_id)
        robots_status[robot_id] = {
            "status": robot_data["status"],
            "task": robot_data.get("task"),
            "current_step": assignment.get("current_step", 0) if assignment else 0,
            "total_steps": len(assignment.get("action_plan", [])) if assignment else 0
        }
    
    return {
        "active": ai_coordinator.mission_state["active"],
        "incidents": {
            "total": len(ai_coordinator.mission_state["incidents"]),
            "list": ai_coordinator.mission_state["incidents"]
        },
        "robots": robots_status,
        "assignments": ai_coordinator.mission_state["assignments"],
        "completed": ai_coordinator.mission_state["completed"]
    }


@router.post("/stop")
def stop_mission():
    """Stop the current mission."""
    ai_coordinator = get_ai_coordinator()
    
    ai_coordinator.mission_state["active"] = False
    logger.info("🛑 Mission stopped")
    
    return {
        "status": "mission_stopped",
        "timestamp": time.time(),
        "summary": {
            "incidents_handled": len(ai_coordinator.mission_state["incidents"]),
            "robots_deployed": len(ai_coordinator.mission_state["assignments"])
        }
    }


@router.get("/report")
def generate_mission_report():
    """Generate comprehensive mission report."""
    ai_coordinator = get_ai_coordinator()
    
    return {
        "mission_active": ai_coordinator.mission_state["active"],
        "incidents": ai_coordinator.mission_state["incidents"],
        "robot_assignments": ai_coordinator.mission_state["assignments"],
        "completed_tasks": ai_coordinator.mission_state["completed"],
        "robots": ai_coordinator.mission_state["robots"],
        "timestamp": time.time()
    }
