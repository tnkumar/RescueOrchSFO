"""Tiago controller #1 that polls Rescue Command Center API and applies all commands."""

import json
import math
import os
import urllib.request
import urllib.error
from controller import Robot

# Use 127.0.0.1 (more reliable than localhost on some systems). Override with RESCUE_API_URL env.
DEFAULT_API = os.environ.get("RESCUE_API_URL", "http://127.0.0.1:8000")
WHEEL_RADIUS = 0.0985
WHEEL_BASE = 0.4044  # distance between wheels

def fetch_command(api_url, robot_id="1"):
    try:
        req = urllib.request.Request(f"{api_url}/tiago/{robot_id}/command")
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return None


def send_position(api_url, robot_id, x, y, z):
    """Send position to backend for UI display."""
    try:
        url = f"{api_url}/tiago/{robot_id}/position"
        data = json.dumps({"x": x, "y": y, "z": z}).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=0.3) as resp:
            pass
    except (urllib.error.URLError, OSError):
        pass


def post_move_to_done(api_url, robot_id):
    """Notify backend that move_to target was reached."""
    try:
        req = urllib.request.Request(f"{api_url}/tiago/{robot_id}/move_to_done", data=b"{}", method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=0.5) as resp:
            pass
    except (urllib.error.URLError, OSError):
        pass


def _angle_norm(a):
    """Normalize angle to [-pi, pi]."""
    while a > math.pi:
        a -= 2 * math.pi
    while a < -math.pi:
        a += 2 * math.pi
    return a


def main():
    robot = Robot()
    timestep = int(robot.getBasicTimeStep())
    
    print("[tiago_api_1] Initializing Tiago robot controller...")

    # Base wheels
    wheel_left = robot.getDevice("wheel_left_joint")
    wheel_right = robot.getDevice("wheel_right_joint")
    wheel_left.setPosition(float("inf"))
    wheel_right.setPosition(float("inf"))
    print("[tiago_api_1] ✓ Wheels initialized")

    # Head joints
    head_1 = robot.getDevice("head_1_joint")
    head_2 = robot.getDevice("head_2_joint")
    head_1.setPosition(0)
    head_2.setPosition(0)
    print("[tiago_api_1] ✓ Head joints initialized")

    # Torso lift
    torso_lift = robot.getDevice("torso_lift_joint")
    torso_lift.setPosition(0)
    print("[tiago_api_1] ✓ Torso lift initialized")

    # Right arm joints
    arm_right_joints = [
        robot.getDevice("arm_right_1_joint"),
        robot.getDevice("arm_right_2_joint"),
        robot.getDevice("arm_right_3_joint"),
        robot.getDevice("arm_right_4_joint"),
        robot.getDevice("arm_right_5_joint"),
        robot.getDevice("arm_right_6_joint"),
        robot.getDevice("arm_right_7_joint"),
    ]
    for joint in arm_right_joints:
        joint.setPosition(0)
    print("[tiago_api_1] ✓ Right arm joints initialized")

    # Left arm joints
    arm_left_joints = [
        robot.getDevice("arm_left_1_joint"),
        robot.getDevice("arm_left_2_joint"),
        robot.getDevice("arm_left_3_joint"),
        robot.getDevice("arm_left_4_joint"),
        robot.getDevice("arm_left_5_joint"),
        robot.getDevice("arm_left_6_joint"),
        robot.getDevice("arm_left_7_joint"),
    ]
    for joint in arm_left_joints:
        joint.setPosition(0)
    print("[tiago_api_1] ✓ Left arm joints initialized")

    # Astra RGBD camera - must enable for camera panels to display
    try:
        rgb_camera = robot.getDevice("Astra rgb")
        rgb_camera.enable(timestep)
        print("[tiago_api_1] ✓ Astra rgb camera enabled")
    except Exception:
        print("[tiago_api_1] ⚠ Astra rgb camera not found")
    try:
        depth_camera = robot.getDevice("Astra depth")
        depth_camera.enable(timestep)
        print("[tiago_api_1] ✓ Astra depth camera enabled")
    except Exception:
        print("[tiago_api_1] ⚠ Astra depth camera not found")

    # Grippers (if available) - Tiago++ proto uses right_hand_gripper_right_finger_joint / left_hand_gripper_right_finger_joint
    gripper_left = None
    gripper_right = None
    for left_name, right_name in [
        ("gripper_left_finger_joint", "gripper_right_finger_joint"),
        ("left_hand_gripper_right_finger_joint", "right_hand_gripper_right_finger_joint"),
    ]:
        try:
            gripper_left = robot.getDevice(left_name)
            gripper_right = robot.getDevice(right_name)
            print(f"[tiago_api_1] ✓ Grippers initialized ({left_name}, {right_name})")
            break
        except Exception:
            pass
    if gripper_left is None and gripper_right is None:
        print("[tiago_api_1] ⚠ Grippers not available on this model")

    # Get API URL: controller args > RESCUE_API_URL env > default
    try:
        args = robot.getControllerArguments()
        api_url = (args[0] if isinstance(args, (list, tuple)) and args else args or DEFAULT_API) or DEFAULT_API
    except Exception:
        api_url = DEFAULT_API
    if not api_url.startswith("http"):
        api_url = DEFAULT_API

    poll_counter = 0
    cmd = None
    linear_x = linear_y = angular = 0.0
    api_connected = False
    last_torso_height = 0.0  # clamp to >= 0 every step to avoid "too low requested position" from world state
    last_gripper_left = 0.0
    last_gripper_right = 0.0
    last_move_to_target = None  # (tx, ty) when in move_to; None after arrival (so next move_to homes arms)

    # Home positions for arms - adjusted to be within joint limits
    arm_home_positions = {
        "right": [0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        "left": [0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    }

    print(f"[tiago_api_1] Polling API at {api_url}/tiago/1/command (ensure backend is running: ./run_backend.sh)")

    warn_counter = 0
    while robot.step(timestep) != -1:
        poll_counter += 1
        warn_counter += 1

        # Poll API every timestep (~8ms) for immediate response
        if poll_counter >= 1:
            poll_counter = 0
            cmd = fetch_command(api_url, "1")
            if cmd and not api_connected:
                api_connected = True
                print("[tiago_api_1] Connected to Rescue Command Center API")
            elif not cmd and not api_connected and warn_counter >= 250:
                warn_counter = 0
                print("[tiago_api_1] ⚠ Backend not reachable at", api_url, "- start backend with ./run_backend.sh")

            if cmd:
                cmd_type = cmd.get("type")
                data = cmd.get("data", {})

                if cmd_type == "velocity":
                    linear_x = data.get("linear_x", 0)
                    linear_y = data.get("linear_y", 0)
                    angular = data.get("angular", 0)
                    print(f"[tiago_api_1] 🚀 VELOCITY command: linear_x={linear_x:.2f}, linear_y={linear_y:.2f}, angular={angular:.2f}")
                elif cmd_type == "action":
                    action = data.get("action", "")
                    print(f"[tiago_api_1] ⚡ ACTION command: {action}")
                    if action == "stop":
                        linear_x = linear_y = angular = 0.0
                        print("[tiago_api_1]   → Stopping all movement")
                    elif action == "home_arms":
                        # Set both arms to home position
                        for i, pos in enumerate(arm_home_positions["right"]):
                            arm_right_joints[i].setPosition(pos)
                        for i, pos in enumerate(arm_home_positions["left"]):
                            arm_left_joints[i].setPosition(pos)
                        print("[tiago_api_1]   → Moving arms to home position")
                elif cmd_type == "head":
                    h1 = data.get("head_1", 0)
                    h2 = data.get("head_2", 0)
                    head_1.setPosition(h1)
                    head_2.setPosition(h2)
                    print(f"[tiago_api_1] 👀 HEAD command: pan={h1:.2f}, tilt={h2:.2f}")
                elif cmd_type == "torso":
                    last_torso_height = max(0.0, data.get("height", 0))
                    torso_lift.setPosition(last_torso_height)
                    print(f"[tiago_api_1] ⬆️ TORSO command: height={last_torso_height:.2f}m")
                elif cmd_type == "arm":
                    arm_side = data.get("arm", "right")
                    joint_positions = data.get("joint_positions")
                    if joint_positions and len(joint_positions) == 7:
                        target_joints = arm_right_joints if arm_side == "right" else arm_left_joints
                        for i, pos in enumerate(joint_positions):
                            target_joints[i].setPosition(pos)
                        print(f"[tiago_api_1] 🦾 ARM command: {arm_side} arm → {joint_positions}")
                elif cmd_type == "gripper":
                    arm_side = data.get("arm", "right")
                    action = data.get("action", "close")
                    pos = max(0.0, 0.045 if action == "open" else 0.0)
                    if arm_side == "right" and gripper_right is not None:
                        last_gripper_right = pos
                        gripper_right.setPosition(pos)
                        print(f"[tiago_api_1] ✋ GRIPPER command: {arm_side} → {'OPEN' if action == 'open' else 'CLOSE'}")
                    elif arm_side == "left" and gripper_left is not None:
                        last_gripper_left = pos
                        gripper_left.setPosition(pos)
                        print(f"[tiago_api_1] ✋ GRIPPER command: {arm_side} → {'OPEN' if action == 'open' else 'CLOSE'}")
                elif cmd_type == "move_to":
                    # Drive to (target_x, target_y) at speed using current_position from backend
                    pos = cmd.get("current_position") or {}
                    if "x" not in pos and "y" not in pos:
                        linear_x = linear_y = angular = 0.0  # wait for supervisor to report position
                    else:
                        cx = pos.get("x", 0.0)
                        cy = pos.get("y", 0.0)
                        yaw = pos.get("yaw", 0.0)
                        tx = data.get("target_x", cx)
                        ty = data.get("target_y", cy)
                        target_key = (round(tx, 2), round(ty, 2))
                        if last_move_to_target != target_key:
                            for i, p in enumerate(arm_home_positions["right"]):
                                arm_right_joints[i].setPosition(p)
                            for i, p in enumerate(arm_home_positions["left"]):
                                arm_left_joints[i].setPosition(p)
                            last_move_to_target = target_key
                            print("[tiago_api_1]   → Arms to home before move")
                        speed = max(0.3, min(1.5, float(data.get("speed", 1.1))))
                        dx = tx - cx
                        dy = ty - cy
                        dist = math.sqrt(dx * dx + dy * dy)
                        ARRIVAL_DIST = 0.25
                        if dist < ARRIVAL_DIST:
                            linear_x = linear_y = angular = 0.0
                            last_move_to_target = None
                            post_move_to_done(api_url, "1")
                            print("[tiago_api_1] 🎯 move_to arrived — stopped (no move, no rotate)")
                        else:
                            desired = math.atan2(dy, dx)
                            angle_err = _angle_norm(desired - yaw)
                            if abs(angle_err) >= 0.12:
                                angular = max(-0.8, min(0.8, 1.0 * angle_err))
                                linear_x = 0.0
                                linear_y = 0.0
                            else:
                                angular = 0.0
                                linear_x = speed
                                linear_y = 0.0

        # Differential drive: v_left = linear - angular * L/2, v_right = linear + angular * L/2
        # Convert m/s to rad/s: omega = v / r
        left_vel = (linear_x - angular * WHEEL_BASE / 2) / WHEEL_RADIUS
        right_vel = (linear_x + angular * WHEEL_BASE / 2) / WHEEL_RADIUS

        wheel_left.setVelocity(max(-10, min(10, left_vel)))
        wheel_right.setVelocity(max(-10, min(10, right_vel)))

        # Re-apply torso and gripper positions >= 0 every step to avoid "too low requested position" (world saved state)
        torso_lift.setPosition(max(0.0, last_torso_height))
        if gripper_left is not None:
            gripper_left.setPosition(max(0.0, last_gripper_left))
        if gripper_right is not None:
            gripper_right.setPosition(max(0.0, last_gripper_right))

        # Position is reported to the backend by the supervisor; Robot has no getPosition() in Webots Python API


if __name__ == "__main__":
    main()

