"""Tiago robot control API endpoints."""

import logging
from fastapi import APIRouter, HTTPException
from app.schemas import (
    TiagoVelocityCommand,
    TiagoArmCommand,
    TiagoHeadCommand,
    TiagoTorsoCommand,
    TiagoGripperCommand,
    TiagoActionCommand,
    TiagoStatus,
    PositionUpdate,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tiago", tags=["Tiago Robot"])

# In-memory state for multiple Tiago robots (replace with Webots controller integration)
_states = {
    "1": {"connected": True, "position": None, "last_command": None},
    "2": {"connected": True, "position": None, "last_command": None},
    "3": {"connected": True, "position": None, "last_command": None},
}


def _get_state(robot_id: str = "1"):
    """Get state for a specific robot, defaulting to robot 1."""
    if robot_id not in _states:
        robot_id = "1"
    return _states[robot_id]


@router.get("/{robot_id}/status", response_model=TiagoStatus)
@router.get("/status", response_model=TiagoStatus)
def get_tiago_status(robot_id: str = "1"):
    """Get current Tiago robot status. robot_id: 1, 2, or 3."""
    state = _get_state(robot_id)
    return TiagoStatus(
        connected=state["connected"],
        position=state["position"],
        battery=100.0,
    )


@router.post("/{robot_id}/position")
def update_tiago_position(robot_id: str, pos: PositionUpdate):
    """Receive position update from Webots controller (optional yaw for move_to driving)."""
    state = _get_state(robot_id)
    state["position"] = {
        "x": round(pos.x, 4), "y": round(pos.y, 4), "z": round(pos.z, 4),
        **({"yaw": round(pos.yaw, 4)} if pos.yaw is not None else {}),
    }
    return {"status": "ok", "robot_id": robot_id}


@router.post("/{robot_id}/velocity")
@router.post("/velocity")
def set_tiago_velocity(cmd: TiagoVelocityCommand, robot_id: str = "1"):
    """
    Set base velocity for Tiago robot.
    linear_x: forward/backward, linear_y: strafe, angular: rotation.
    robot_id: 1, 2, or 3.
    """
    state = _get_state(robot_id)
    state["last_command"] = {"type": "velocity", "data": cmd.model_dump()}
    logger.info(f"📥 TIAGO-{robot_id} VELOCITY command received: linear_x={cmd.linear_x:.2f}, linear_y={cmd.linear_y:.2f}, angular={cmd.angular:.2f}")
    return {"status": "ok", "command": state["last_command"], "robot_id": robot_id}


@router.post("/{robot_id}/arm")
@router.post("/arm")
def set_tiago_arm(cmd: TiagoArmCommand, robot_id: str = "1"):
    """Command Tiago arm to a position or pose. robot_id: 1, 2, or 3."""
    if cmd.arm not in ("left", "right"):
        raise HTTPException(400, f"Invalid arm: {cmd.arm}")
    state = _get_state(robot_id)
    state["last_command"] = {"type": "arm", "data": cmd.model_dump()}
    logger.info(f"📥 TIAGO-{robot_id} ARM command received: {cmd.arm} arm, positions={cmd.joint_positions}")
    return {"status": "ok", "command": state["last_command"], "robot_id": robot_id}


@router.post("/{robot_id}/head")
@router.post("/head")
def set_tiago_head(cmd: TiagoHeadCommand, robot_id: str = "1"):
    """Control Tiago head pan and tilt. robot_id: 1, 2, or 3."""
    state = _get_state(robot_id)
    state["last_command"] = {"type": "head", "data": cmd.model_dump()}
    logger.info(f"📥 TIAGO-{robot_id} HEAD command received: pan={cmd.head_1:.2f}, tilt={cmd.head_2:.2f}")
    return {"status": "ok", "command": state["last_command"], "robot_id": robot_id}


@router.post("/{robot_id}/torso")
@router.post("/torso")
def set_tiago_torso(cmd: TiagoTorsoCommand, robot_id: str = "1"):
    """Control Tiago torso lift height. robot_id: 1, 2, or 3."""
    state = _get_state(robot_id)
    state["last_command"] = {"type": "torso", "data": cmd.model_dump()}
    logger.info(f"📥 TIAGO-{robot_id} TORSO command received: height={cmd.height:.2f}m")
    return {"status": "ok", "command": state["last_command"], "robot_id": robot_id}


@router.post("/{robot_id}/gripper")
@router.post("/gripper")
def set_tiago_gripper(cmd: TiagoGripperCommand, robot_id: str = "1"):
    """Control Tiago gripper (open/close). robot_id: 1, 2, or 3."""
    if cmd.arm not in ("left", "right"):
        raise HTTPException(400, f"Invalid arm: {cmd.arm}")
    if cmd.action not in ("open", "close"):
        raise HTTPException(400, f"Invalid action: {cmd.action}. Must be 'open' or 'close'")
    state = _get_state(robot_id)
    state["last_command"] = {"type": "gripper", "data": cmd.model_dump()}
    logger.info(f"📥 TIAGO-{robot_id} GRIPPER command received: {cmd.arm} → {cmd.action.upper()}")
    return {"status": "ok", "command": state["last_command"], "robot_id": robot_id}


@router.post("/{robot_id}/action")
@router.post("/action")
def tiago_action(cmd: TiagoActionCommand, robot_id: str = "1"):
    """Execute action: stop, home_arms, open_gripper, close_gripper. robot_id: 1, 2, or 3."""
    valid = ("stop", "home_arms", "open_gripper", "close_gripper")
    if cmd.action not in valid:
        raise HTTPException(400, f"Invalid action: {cmd.action}. Must be one of: {valid}")
    state = _get_state(robot_id)
    state["last_command"] = {"type": "action", "data": cmd.model_dump()}
    logger.info(f"📥 TIAGO-{robot_id} ACTION command received: {cmd.action.upper()}")
    return {"status": "ok", "action": cmd.action, "robot_id": robot_id}


@router.post("/{robot_id}/stop")
@router.post("/stop")
def tiago_stop(robot_id: str = "1"):
    """Convenience endpoint: stop Tiago base movement. robot_id: 1, 2, or 3."""
    logger.info(f"📥 TIAGO-{robot_id} STOP endpoint called")
    return tiago_action(TiagoActionCommand(action="stop"), robot_id=robot_id)


@router.post("/{robot_id}/move_to")
def tiago_move_to(robot_id: str, x: float, y: float, speed: float = 1.1):
    """
    Command Tiago to drive to (x, y) at a constant speed instead of teleporting.
    Controller drives straight after pointing; stops (no move, no rotate) at destination.
    """
    if robot_id not in ("1", "2", "3"):
        raise HTTPException(400, "robot_id must be 1, 2, or 3")
    state = _get_state(robot_id)
    state["last_command"] = {
        "type": "move_to",
        "data": {"target_x": float(x), "target_y": float(y), "speed": max(0.3, min(1.5, float(speed)))},
    }
    logger.info(f"📥 TIAGO-{robot_id} MOVE TO ({x:.2f}, {y:.2f}) at speed {speed:.2f} m/s")
    return {"status": "ok", "robot_id": robot_id, "target": {"x": x, "y": y}, "speed": speed}


@router.post("/{robot_id}/move_to_done")
def tiago_move_to_done(robot_id: str):
    """Called by Webots controller when Tiago has reached the move_to target."""
    state = _get_state(robot_id)
    if state.get("last_command", {}).get("type") == "move_to":
        state["last_command"] = {"type": "velocity", "data": {"linear_x": 0, "linear_y": 0, "angular": 0}}
        logger.info(f"📥 TIAGO-{robot_id} move_to completed (arrived)")
    return {"status": "ok", "robot_id": robot_id}


@router.get("/{robot_id}/command")
@router.get("/command")
def get_tiago_command(robot_id: str = "1"):
    """Get last command for Webots controller to poll. robot_id: 1, 2, or 3."""
    state = _get_state(robot_id)
    cmd = state.get("last_command") or {"type": "velocity", "data": {"linear_x": 0, "linear_y": 0, "angular": 0}}
    # For move_to, include current position so controller can compute velocity (from supervisor-reported position)
    if cmd.get("type") == "move_to" and state.get("position"):
        out = dict(cmd)
        out["current_position"] = state["position"]
        logger.debug(f"🔄 TIAGO-{robot_id} poll → move_to with position {state['position']}")
        return out
    logger.debug(f"🔄 TIAGO-{robot_id} poll → {cmd.get('type')}")
    return cmd
