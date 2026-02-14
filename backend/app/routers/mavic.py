"""Mavic drone control API endpoints."""

from __future__ import annotations

import asyncio
import io
import logging
import threading
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from PIL import Image
from app.schemas import (
    MavicVelocityCommand,
    MavicAltitudeCommand,
    MavicActionCommand,
    MavicStatus,
    PositionUpdate,
)
from app.services.dependencies import get_ai_coordinator

router = APIRouter(
    prefix="/mavic",
    tags=["Mavic Control"],
    responses={404: {"description": "Not found"}},
)

# In-memory state (replace with Webots controller integration)
_state = {"flying": False, "altitude": 0.0, "connected": True, "last_command": None, "position": None}

# Camera stream state
_camera_frame: Optional[bytes] = None
_camera_lock = threading.Lock()


@router.get("/status", response_model=MavicStatus)
def get_mavic_status():
    """Get current Mavic drone status."""
    pos = _state.get("position")
    if pos is None and _state["flying"]:
        pos = {"x": 0.0, "y": 0.0, "z": _state["altitude"]}
    return MavicStatus(
        connected=_state["connected"],
        flying=_state["flying"],
        altitude=_state["altitude"],
        position=pos,
    )


@router.post("/position")
def update_mavic_position(pos: PositionUpdate):
    """Receive position update from Webots controller (GPS)."""
    global _state
    _state["position"] = {"x": round(pos.x, 4), "y": round(pos.y, 4), "z": round(pos.z, 4)}
    _state["altitude"] = pos.z
    return {"status": "ok"}


@router.post("/velocity")
def set_mavic_velocity(cmd: MavicVelocityCommand):
    """
    Set velocity commands for Mavic drone.
    Pitch: forward/backward, Roll: strafe, Yaw: rotate, Vertical: altitude change.
    """
    _state["last_command"] = {"type": "velocity", "data": cmd.model_dump()}
    logger.info(f"📥 MAVIC VELOCITY command received: pitch={cmd.pitch:.2f}, roll={cmd.roll:.2f}, yaw={cmd.yaw:.2f}, vertical={cmd.vertical:.2f}")
    return {"status": "ok", "command": _state["last_command"]}


@router.post("/altitude")
def set_mavic_altitude(cmd: MavicAltitudeCommand):
    """Set target altitude for Mavic drone in meters."""
    _state["altitude"] = cmd.altitude
    _state["last_command"] = {"type": "altitude", "data": cmd.model_dump()}
    logger.info(f"📥 MAVIC ALTITUDE command received: {cmd.altitude:.2f}m")
    return {"status": "ok", "target_altitude": cmd.altitude}


@router.post("/action")
def mavic_action(cmd: MavicActionCommand):
    """Execute action: takeoff, land, or hover."""
    if cmd.action not in ("takeoff", "land", "hover"):
        raise HTTPException(400, f"Invalid action: {cmd.action}")
    _state["flying"] = cmd.action == "takeoff" or (_state["flying"] and cmd.action != "land")
    if cmd.action == "takeoff" and _state["altitude"] < 0.5:
        _state["altitude"] = 1.0
    elif cmd.action == "land":
        _state["altitude"] = 0.0
    _state["last_command"] = {"type": "action", "data": cmd.model_dump()}
    logger.info(f"📥 MAVIC ACTION command received: {cmd.action.upper()}, flying={_state['flying']}")
    return {"status": "ok", "action": cmd.action, "flying": _state["flying"]}


@router.post("/takeoff")
def mavic_takeoff():
    """Convenience endpoint: command Mavic to take off."""
    logger.info("📥 MAVIC TAKEOFF endpoint called")
    return mavic_action(MavicActionCommand(action="takeoff"))


@router.post("/land")
def mavic_land():
    """Convenience endpoint: command Mavic to land."""
    logger.info("📥 MAVIC LAND endpoint called")
    return mavic_action(MavicActionCommand(action="land"))


@router.post("/hover")
def mavic_hover():
    """Convenience endpoint: command Mavic to hover in place."""
    logger.info("📥 MAVIC HOVER endpoint called")
    return mavic_action(MavicActionCommand(action="hover"))


@router.get("/command")
def get_mavic_command():
    """Get last command for Webots controller to poll."""
    global _state
    cmd = _state.get("last_command") or {"type": "velocity", "data": {"pitch": 0, "roll": 0, "yaw": 0, "vertical": 0}}
    logger.debug(f"🔄 Controller polling /mavic/command → returning: {cmd.get('type')}")
    
    # Clear action commands after they're read once (to prevent re-processing)
    if cmd.get("type") == "action":
        _state["last_command"] = None
    
    return {
        **cmd,
        "target_altitude": _state["altitude"],
        "flying": _state["flying"],
    }



def _process_frame_sync(body_bytes: bytes, width: int, height: int) -> bytes:
    """Process raw image bytes to JPEG (CPU bound)."""
    expected_bgra = width * height * 4
    expected_rgb = width * height * 3
    
    if len(body_bytes) == expected_bgra:
        try:
            # Try RGBX (4 bytes per pixel, ignore alpha)
            # Webots BGRA -> PIL RGBX (B=R, G=G, R=B) -> Swap channels
            img = Image.frombytes("RGBX", (width, height), body_bytes)
            # R, G, B, X = img.split() # No, RGBX splits to R, G, B (X is ignored)
            # Actually, split() on RGBX gives R,G,B? Let's check docs or be safe.
            # Convert to RGBA first to be sure
            img = img.convert("RGBA")
            r, g, b, a = img.split()
            # If input was BGRA: R=B, G=G, B=R. So we swap R and B.
            img = Image.merge("RGB", (b, g, r))
        except Exception as e1:
            logger.warning(f"⚠️ Primary BGRA decode failed: {e1}. Trying fallback RGBA.")
            try:
                # Fallback: Just load as RGBA and convert
                img = Image.frombytes("RGBA", (width, height), body_bytes).convert("RGB")
            except Exception as e2:
                logger.error(f"❌ Secondary decode failed: {e2}. Returning black frame.")
                img = Image.new("RGB", (width, height), (0, 0, 0))
        rgb = img
    elif len(body_bytes) == expected_rgb:
        img = Image.frombytes("RGB", (width, height), body_bytes)
        rgb = img
    else:
        # Avoid complex logic for now, just log and fail gracefully
        logger.error(f"❌ Size mismatch: {len(body_bytes)}. Expected {expected_bgra} (BGRA) or {expected_rgb} (RGB). Returning Black Frame.")
        rgb = Image.new("RGB", (width, height), (0, 0, 0))

    buf = io.BytesIO()
    rgb.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


@router.post("/camera/frame")
async def receive_camera_frame(request: Request):
    """Receive raw BGRA frame from Webots controller."""
    width = int(request.query_params.get("width", 400))
    height = int(request.query_params.get("height", 240))
    body = await request.body()
    
    # Log at DEBUG level to avoid spam
    if hasattr(logger, "debug"):
        logger.debug(f"📸 Frame received: {len(body)} bytes")
    
    try:
        # Offload CPU-intensive image processing to thread pool
        loop = asyncio.get_event_loop()
        jpeg = await loop.run_in_executor(None, _process_frame_sync, bytes(body), width, height)
        
        with _camera_lock:
            global _camera_frame  # noqa: PLW0603
            _camera_frame = jpeg
            
    except Exception as e:
        logger.error(f"❌ Frame processing error: {e}")
        # Don't crash the controller, just return error
        return {"status": "error", "message": str(e)}
        
    return {"status": "ok", "size": len(jpeg)}


async def _mjpeg_stream():
    """Async generator yielding MJPEG multipart stream."""
    boundary = b"--frame"
    while True:
        await asyncio.sleep(0.033)  # ~30 FPS cap
        with _camera_lock:
            frame = _camera_frame
        
        if frame:
            yield (
                boundary + b"\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(frame)).encode() + b"\r\n"
                b"\r\n" + frame + b"\r\n"
            )
        else:
            # Yield empty frame or keep alive? Better to just wait.
            pass


@router.get("/camera/stream")
async def mavic_camera_stream():
    """MJPEG stream of Mavic camera feed."""
    return StreamingResponse(
        _mjpeg_stream(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
