"""Tiago controller #3 that polls Rescue Command Center API and applies all commands."""

import json
import urllib.request
import urllib.error
from controller import Robot

# Use 127.0.0.1 (more reliable than localhost on some systems)
DEFAULT_API = "http://127.0.0.1:8000"
WHEEL_RADIUS = 0.0985
WHEEL_BASE = 0.4044  # distance between wheels

def fetch_command(api_url, robot_id="3"):
    try:
        req = urllib.request.Request(f"{api_url}/tiago/{robot_id}/command")
        with urllib.request.urlopen(req, timeout=0.5) as resp:
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


def main():
    robot = Robot()
    timestep = int(robot.getBasicTimeStep())
    
    print("[tiago_api_3] Initializing Tiago robot controller...")

    # Base wheels
    wheel_left = robot.getDevice("wheel_left_joint")
    wheel_right = robot.getDevice("wheel_right_joint")
    wheel_left.setPosition(float("inf"))
    wheel_right.setPosition(float("inf"))
    print("[tiago_api_3] ✓ Wheels initialized")

    # Head joints
    head_1 = robot.getDevice("head_1_joint")
    head_2 = robot.getDevice("head_2_joint")
    head_1.setPosition(0)
    head_2.setPosition(0)
    print("[tiago_api_3] ✓ Head joints initialized")

    # Torso lift
    torso_lift = robot.getDevice("torso_lift_joint")
    torso_lift.setPosition(0)
    print("[tiago_api_3] ✓ Torso lift initialized")

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
    print("[tiago_api_3] ✓ Right arm joints initialized")

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
    print("[tiago_api_3] ✓ Left arm joints initialized")

    # Astra RGBD camera - must enable for camera panels to display
    try:
        rgb_camera = robot.getDevice("Astra rgb")
        rgb_camera.enable(timestep)
        print("[tiago_api_3] ✓ Astra rgb camera enabled")
    except Exception:
        print("[tiago_api_3] ⚠ Astra rgb camera not found")
    try:
        depth_camera = robot.getDevice("Astra depth")
        depth_camera.enable(timestep)
        print("[tiago_api_3] ✓ Astra depth camera enabled")
    except Exception:
        print("[tiago_api_3] ⚠ Astra depth camera not found")

    # Grippers (if available) - Tiago++ uses different naming
    gripper_left = None
    gripper_right = None
    try:
        # Try standard Tiago++ gripper names
        gripper_left = robot.getDevice("gripper_left_finger_joint")
        gripper_right = robot.getDevice("gripper_right_finger_joint")
        print("[tiago_api_3] ✓ Grippers initialized")
    except:
        print("[tiago_api_3] ⚠ Grippers not available on this model")
        pass

    # Get API URL from controller args (optional)
    try:
        args = robot.getControllerArguments()
        api_url = (args[0] if isinstance(args, (list, tuple)) and args else args or DEFAULT_API) or DEFAULT_API
    except Exception:
        api_url = DEFAULT_API

    poll_counter = 0
    pos_counter = 0
    cmd = None
    linear_x = linear_y = angular = 0.0
    api_connected = False

    # Home positions for arms - adjusted to be within joint limits
    arm_home_positions = {
        "right": [0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0],
        "left": [0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0]
    }

    print(f"[tiago_api_3] Polling API at {api_url}/tiago/3/command")

    while robot.step(timestep) != -1:
        poll_counter += 1

        # Poll API every timestep (~8ms) for immediate response
        if poll_counter >= 1:
            poll_counter = 0
            cmd = fetch_command(api_url, "3")
            if cmd and not api_connected:
                api_connected = True
                print("[tiago_api_3] Connected to Rescue Command Center API")

            if cmd:
                cmd_type = cmd.get("type")
                data = cmd.get("data", {})

                if cmd_type == "velocity":
                    linear_x = data.get("linear_x", 0)
                    linear_y = data.get("linear_y", 0)
                    angular = data.get("angular", 0)
                    print(f"[tiago_api_3] 🚀 VELOCITY command: linear_x={linear_x:.2f}, linear_y={linear_y:.2f}, angular={angular:.2f}")
                elif cmd_type == "action":
                    action = data.get("action", "")
                    print(f"[tiago_api_3] ⚡ ACTION command: {action}")
                    if action == "stop":
                        linear_x = linear_y = angular = 0.0
                        print("[tiago_api_3]   → Stopping all movement")
                    elif action == "home_arms":
                        # Set both arms to home position
                        for i, pos in enumerate(arm_home_positions["right"]):
                            arm_right_joints[i].setPosition(pos)
                        for i, pos in enumerate(arm_home_positions["left"]):
                            arm_left_joints[i].setPosition(pos)
                        print("[tiago_api_3]   → Moving arms to home position")
                elif cmd_type == "head":
                    h1 = data.get("head_1", 0)
                    h2 = data.get("head_2", 0)
                    head_1.setPosition(h1)
                    head_2.setPosition(h2)
                    print(f"[tiago_api_3] 👀 HEAD command: pan={h1:.2f}, tilt={h2:.2f}")
                elif cmd_type == "torso":
                    height = data.get("height", 0)
                    torso_lift.setPosition(height)
                    print(f"[tiago_api_3] ⬆️ TORSO command: height={height:.2f}m")
                elif cmd_type == "arm":
                    arm_side = data.get("arm", "right")
                    joint_positions = data.get("joint_positions")
                    if joint_positions and len(joint_positions) == 7:
                        target_joints = arm_right_joints if arm_side == "right" else arm_left_joints
                        for i, pos in enumerate(joint_positions):
                            target_joints[i].setPosition(pos)
                        print(f"[tiago_api_3] 🦾 ARM command: {arm_side} arm → {joint_positions}")
                elif cmd_type == "gripper":
                    arm_side = data.get("arm", "right")
                    action = data.get("action", "close")
                    gripper = gripper_right if arm_side == "right" else gripper_left
                    if gripper:
                        if action == "open":
                            gripper.setPosition(0.045)  # Open position
                            print(f"[tiago_api_3] ✋ GRIPPER command: {arm_side} → OPEN")
                        elif action == "close":
                            gripper.setPosition(0.0)  # Closed position
                            print(f"[tiago_api_3] ✊ GRIPPER command: {arm_side} → CLOSE")

        # Differential drive: v_left = linear - angular * L/2, v_right = linear + angular * L/2
        # Convert m/s to rad/s: omega = v / r
        left_vel = (linear_x - angular * WHEEL_BASE / 2) / WHEEL_RADIUS
        right_vel = (linear_x + angular * WHEEL_BASE / 2) / WHEEL_RADIUS

        wheel_left.setVelocity(max(-10, min(10, left_vel)))
        wheel_right.setVelocity(max(-10, min(10, right_vel)))

        # Send position to backend for UI (~4 times/sec)
        pos_counter += 1
        if pos_counter >= 31:
            pos_counter = 0
            pos = robot.getPosition()
            if pos and len(pos) >= 3:
                send_position(api_url, "3", pos[0], pos[1], pos[2])


if __name__ == "__main__":
    main()
