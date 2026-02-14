"""Supervisor control router - Complete API for centralized robot manipulation."""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/supervisor", tags=["Supervisor Control"])

# In-memory command state
_command = None


# ========== PYDANTIC MODELS ==========

class Position(BaseModel):
    x: float = Field(..., description="X coordinate in meters")
    y: float = Field(..., description="Y coordinate in meters")
    z: float = Field(..., description="Z coordinate in meters")


class Velocity(BaseModel):
    vx: float = Field(0, description="Linear velocity X (m/s)")
    vy: float = Field(0, description="Linear velocity Y (m/s)")
    vz: float = Field(0, description="Linear velocity Z (m/s)")
    wx: float = Field(0, description="Angular velocity X (rad/s)")
    wy: float = Field(0, description="Angular velocity Y (rad/s)")
    wz: float = Field(0, description="Angular velocity Z (rad/s)")


class Rotation(BaseModel):
    axis_x: float = Field(..., description="Rotation axis X component")
    axis_y: float = Field(..., description="Rotation axis Y component")
    axis_z: float = Field(..., description="Rotation axis Z component")
    angle: float = Field(..., description="Rotation angle in radians")


class TeleportCommand(BaseModel):
    target: str = Field(..., description="Robot name: 'mavic', 'tiago1', 'tiago2', 'tiago3'")
    position: Position


class VelocityCommand(BaseModel):
    target: str = Field(..., description="Robot name: 'mavic', 'tiago1', 'tiago2', 'tiago3'")
    velocity: Velocity


class RotationCommand(BaseModel):
    target: str = Field(..., description="Robot name: 'mavic', 'tiago1', 'tiago2', 'tiago3'")
    rotation: Rotation


class FormationCommand(BaseModel):
    formation_type: str = Field(..., description="Formation: 'line', 'triangle', 'square', 'circle'")
    center_x: float = Field(0, description="Formation center X")
    center_y: float = Field(0, description="Formation center Y")
    z: float = Field(0.095, description="Z height for Tiagos")
    spacing: float = Field(1.5, description="Spacing between robots (meters)")


class MultiRobotCommand(BaseModel):
    commands: List[dict] = Field(..., description="List of commands for multiple robots")


# ========== POSITION CONTROL ENDPOINTS ==========

@router.post("/teleport")
def teleport_robot(cmd: TeleportCommand):
    """
    Teleport a robot to a specific position instantly.
    
    **Targets:**
    - `mavic`: Mavic 2 Pro drone
    - `tiago1`: First Tiago++ robot
    - `tiago2`: Second Tiago++ robot
    - `tiago3`: Third Tiago++ robot
    
    **Example:**
    ```json
    {
        "target": "mavic",
        "position": {"x": 0, "y": 0, "z": 2.0}
    }
    ```
    """
    global _command
    _command = {
        "type": "teleport",
        "target": cmd.target,
        "data": {
            "x": cmd.position.x,
            "y": cmd.position.y,
            "z": cmd.position.z
        }
    }
    logger.info(f"📍 TELEPORT command: {cmd.target} → ({cmd.position.x}, {cmd.position.y}, {cmd.position.z})")
    return {"status": "ok", "command": _command}


@router.get("/position/{target}")
def get_robot_position(target: str):
    """
    Get current position of a robot.
    
    **Note:** This endpoint triggers a position query command. 
    The supervisor will respond with the position in the next poll.
    """
    global _command
    _command = {
        "type": "get_position",
        "target": target,
        "data": {}
    }
    logger.info(f"📍 GET POSITION query: {target}")
    return {"status": "ok", "message": "Position query sent"}


# ========== VELOCITY CONTROL ENDPOINTS ==========

@router.post("/velocity")
def set_robot_velocity(cmd: VelocityCommand):
    """
    Set robot velocity directly (bypasses physics simulation).
    
    **Velocity components:**
    - `vx, vy, vz`: Linear velocity (m/s)
    - `wx, wy, wz`: Angular velocity (rad/s)
    
    **Example - Mavic fly forward:**
    ```json
    {
        "target": "mavic",
        "velocity": {"vx": 1.0, "vy": 0, "vz": 0, "wx": 0, "wy": 0, "wz": 0}
    }
    ```
    
    **Example - Tiago rotate:**
    ```json
    {
        "target": "tiago1",
        "velocity": {"vx": 0, "vy": 0, "vz": 0, "wx": 0, "wy": 0, "wz": 0.5}
    }
    ```
    """
    global _command
    _command = {
        "type": "velocity",
        "target": cmd.target,
        "data": {
            "vx": cmd.velocity.vx,
            "vy": cmd.velocity.vy,
            "vz": cmd.velocity.vz,
            "wx": cmd.velocity.wx,
            "wy": cmd.velocity.wy,
            "wz": cmd.velocity.wz
        }
    }
    logger.info(f"🚀 VELOCITY command: {cmd.target} → v=({cmd.velocity.vx}, {cmd.velocity.vy}, {cmd.velocity.vz})")
    return {"status": "ok", "command": _command}


@router.post("/stop/{target}")
def stop_robot(target: str):
    """
    Stop a robot immediately by resetting its physics.
    
    **Targets:** `mavic`, `tiago1`, `tiago2`, `tiago3`
    """
    global _command
    _command = {
        "type": "stop",
        "target": target,
        "data": {}
    }
    logger.info(f"🛑 STOP command: {target}")
    return {"status": "ok", "command": _command}


@router.post("/stop_all")
def stop_all_robots():
    """Stop all robots immediately."""
    global _command
    _command = {
        "type": "stop_all",
        "target": "all",
        "data": {}
    }
    logger.info("🛑 STOP ALL command")
    return {"status": "ok", "command": _command}


# ========== ROTATION/ORIENTATION CONTROL ==========

@router.post("/rotate")
def rotate_robot(cmd: RotationCommand):
    """
    Set robot rotation/orientation.
    
    **Rotation format:** Axis-angle representation
    - `axis_x, axis_y, axis_z`: Rotation axis (unit vector)
    - `angle`: Rotation angle in radians
    
    **Example - Rotate Mavic 90° around Z-axis:**
    ```json
    {
        "target": "mavic",
        "rotation": {"axis_x": 0, "axis_y": 0, "axis_z": 1, "angle": 1.5708}
    }
    ```
    """
    global _command
    _command = {
        "type": "rotate",
        "target": cmd.target,
        "data": {
            "axis_x": cmd.rotation.axis_x,
            "axis_y": cmd.rotation.axis_y,
            "axis_z": cmd.rotation.axis_z,
            "angle": cmd.rotation.angle
        }
    }
    logger.info(f"🔄 ROTATE command: {cmd.target} → axis=({cmd.rotation.axis_x}, {cmd.rotation.axis_y}, {cmd.rotation.axis_z}), angle={cmd.rotation.angle}")
    return {"status": "ok", "command": _command}


# ========== MULTI-ROBOT COORDINATION ==========

@router.post("/formation")
def set_formation(cmd: FormationCommand):
    """
    Arrange Tiago robots in a formation.
    
    **Formation types:**
    - `line`: Robots in a straight line
    - `triangle`: Robots in triangle formation
    - `square`: Robots in square formation (uses only 3 robots)
    - `circle`: Robots in circular formation
    
    **Example:**
    ```json
    {
        "formation_type": "line",
        "center_x": 0,
        "center_y": 0,
        "z": 0.095,
        "spacing": 2.0
    }
    ```
    """
    global _command
    _command = {
        "type": "formation",
        "target": "tiagos",
        "data": {
            "formation_type": cmd.formation_type,
            "center_x": cmd.center_x,
            "center_y": cmd.center_y,
            "z": cmd.z,
            "spacing": cmd.spacing
        }
    }
    logger.info(f"🎯 FORMATION command: {cmd.formation_type} at ({cmd.center_x}, {cmd.center_y}), spacing={cmd.spacing}")
    return {"status": "ok", "command": _command}


@router.post("/multi_command")
def execute_multi_command(cmd: MultiRobotCommand):
    """
    Execute multiple commands for different robots simultaneously.
    
    **Example:**
    ```json
    {
        "commands": [
            {"type": "teleport", "target": "mavic", "data": {"x": 0, "y": 0, "z": 3}},
            {"type": "velocity", "target": "tiago1", "data": {"vx": 0.5, "vy": 0, "vz": 0}},
            {"type": "stop", "target": "tiago2", "data": {}}
        ]
    }
    ```
    """
    global _command
    _command = {
        "type": "multi_command",
        "target": "multiple",
        "data": {
            "commands": cmd.commands
        }
    }
    logger.info(f"🎛️ MULTI COMMAND: {len(cmd.commands)} commands")
    return {"status": "ok", "command": _command}


# ========== STATUS & MONITORING ==========

@router.get("/status")
def get_all_status():
    """
    Get status of all robots.
    
    **Note:** This triggers a status query. The supervisor will respond with
    positions and velocities in the next poll.
    """
    global _command
    _command = {
        "type": "get_all_status",
        "target": "all",
        "data": {}
    }
    logger.info("📊 GET ALL STATUS query")
    return {"status": "ok", "message": "Status query sent"}


@router.get("/command")
def get_supervisor_command():
    """
    Poll endpoint for supervisor controller to fetch the latest command.
    
    **Returns:** The most recent command or `{"type": "none"}` if no command.
    """
    global _command
    if _command:
        logger.debug(f"🔄 Supervisor polling → returning: {_command.get('type')}")
    return _command or {"type": "none", "target": "none", "data": {}}


@router.delete("/command")
def clear_command():
    """Clear the current command."""
    global _command
    _command = None
    logger.info("🗑️ Command cleared")
    return {"status": "ok", "message": "Command cleared"}


# ========== MAVIC-SPECIFIC ENDPOINTS ==========

@router.post("/mavic/takeoff")
def mavic_takeoff(altitude: float = 2.0):
    """
    Command Mavic to take off to specified altitude.
    
    **Parameters:**
    - `altitude`: Target altitude in meters (default: 2.0)
    """
    global _command
    _command = {
        "type": "teleport",
        "target": "mavic",
        "data": {"x": 0, "y": 0, "z": altitude}
    }
    logger.info(f"🚁 MAVIC TAKEOFF to {altitude}m")
    return {"status": "ok", "altitude": altitude}


@router.post("/mavic/land")
def mavic_land():
    """Command Mavic to land (set altitude to 0.1m)."""
    global _command
    _command = {
        "type": "mavic_land",
        "target": "mavic",
        "data": {}
    }
    logger.info("🚁 MAVIC LAND")
    return {"status": "ok"}


@router.post("/mavic/hover")
def mavic_hover():
    """Command Mavic to hover in place (stop all movement)."""
    global _command
    _command = {
        "type": "stop",
        "target": "mavic",
        "data": {}
    }
    logger.info("🚁 MAVIC HOVER")
    return {"status": "ok"}


# ========== TIAGO-SPECIFIC ENDPOINTS ==========

@router.post("/tiago/{robot_id}/move_to")
def tiago_move_to(robot_id: int, x: float, y: float):
    """
    Command Tiago to move to a position (teleport).
    
    **Parameters:**
    - `robot_id`: 1, 2, or 3
    - `x, y`: Target coordinates
    """
    if robot_id not in [1, 2, 3]:
        raise HTTPException(400, "robot_id must be 1, 2, or 3")
    
    target = f"tiago{robot_id}"
    global _command
    _command = {
        "type": "teleport",
        "target": target,
        "data": {"x": x, "y": y, "z": 0.095}
    }
    logger.info(f"🤖 TIAGO-{robot_id} MOVE TO ({x}, {y})")
    return {"status": "ok", "robot_id": robot_id, "position": {"x": x, "y": y}}


@router.post("/tiago/{robot_id}/forward")
def tiago_move_forward(robot_id: int, speed: float = 0.5):
    """
    Command Tiago to move forward at specified speed.
    
    **Parameters:**
    - `robot_id`: 1, 2, or 3
    - `speed`: Forward speed in m/s (default: 0.5)
    """
    if robot_id not in [1, 2, 3]:
        raise HTTPException(400, "robot_id must be 1, 2, or 3")
    
    target = f"tiago{robot_id}"
    global _command
    _command = {
        "type": "velocity",
        "target": target,
        "data": {"vx": speed, "vy": 0, "vz": 0, "wx": 0, "wy": 0, "wz": 0}
    }
    logger.info(f"🤖 TIAGO-{robot_id} FORWARD at {speed} m/s")
    return {"status": "ok", "robot_id": robot_id, "speed": speed}


@router.post("/tiago/{robot_id}/rotate")
def tiago_rotate(robot_id: int, angular_speed: float = 0.5):
    """
    Command Tiago to rotate at specified angular speed.
    
    **Parameters:**
    - `robot_id`: 1, 2, or 3
    - `angular_speed`: Rotation speed in rad/s (default: 0.5, positive=counterclockwise)
    """
    if robot_id not in [1, 2, 3]:
        raise HTTPException(400, "robot_id must be 1, 2, or 3")
    
    target = f"tiago{robot_id}"
    global _command
    _command = {
        "type": "velocity",
        "target": target,
        "data": {"vx": 0, "vy": 0, "vz": 0, "wx": 0, "wy": 0, "wz": angular_speed}
    }
    logger.info(f"🤖 TIAGO-{robot_id} ROTATE at {angular_speed} rad/s")
    return {"status": "ok", "robot_id": robot_id, "angular_speed": angular_speed}
