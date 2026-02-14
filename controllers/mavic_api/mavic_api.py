"""Mavic controller that polls Rescue Command Center API and applies commands."""

import json
import urllib.request
import urllib.error
from controller import Robot, Camera

DEFAULT_API = "http://127.0.0.1:8000"

# Camera sampling: 64ms (~15 fps) for smoother feed
CAMERA_SAMPLE_PERIOD_MS = 64


def fetch_command(api_url):
    try:
        req = urllib.request.Request(f"{api_url}/mavic/command")
        with urllib.request.urlopen(req, timeout=0.5) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return None


def send_camera_frame(api_url, data, width, height):
    try:
        url = f"{api_url}/mavic/camera/frame?width={width}&height={height}"
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/octet-stream")
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            pass
    except (urllib.error.URLError, OSError):
        pass


def send_position(api_url, x, y, z):
    """Send GPS position to backend for UI display."""
    try:
        url = f"{api_url}/mavic/position"
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
    
    print("[mavic_api] Initializing Mavic 2 Pro controller...")

    # Devices
    imu = robot.getDevice("inertial unit")
    imu.enable(timestep)
    gps = robot.getDevice("gps")
    gps.enable(timestep)
    gyro = robot.getDevice("gyro")
    gyro.enable(timestep)
    camera_roll = robot.getDevice("camera roll")
    camera_pitch = robot.getDevice("camera pitch")
    print("[mavic_api] ✓ Sensors initialized")

    # Camera for live feed
    camera = robot.getDevice("camera")
    if not camera:
        print("[mavic_api] ⚠️ Camera not found by name, searching devices...")
        for i in range(robot.getNumberOfDevices()):
            dev = robot.getDeviceByIndex(i)
            # Check for camera capability (getImage is standard)
            if dev and hasattr(dev, "getImage"):
                camera = dev
                print(f"[mavic_api] ✓ Found camera device at index {i}")
                break
    
    if camera:
        camera.enable(CAMERA_SAMPLE_PERIOD_MS)
        print(f"[mavic_api] ✓ Camera initialized ({camera.getWidth()}x{camera.getHeight()})")
    else:
        print("[mavic_api] ❌ FATAL: No camera device found!")
    front_left_led = robot.getDevice("front left led")
    front_right_led = robot.getDevice("front right led")

    front_left = robot.getDevice("front left propeller")
    front_right = robot.getDevice("front right propeller")
    rear_left = robot.getDevice("rear left propeller")
    rear_right = robot.getDevice("rear right propeller")

    for m in [front_left, front_right, rear_left, rear_right]:
        m.setPosition(float("inf"))
        m.setVelocity(1.0)
    print("[mavic_api] ✓ Propellers initialized")

    # Constants (from mavic2pro C controller)
    K_VERTICAL_THRUST = 68.5
    K_VERTICAL_OFFSET = 0.6
    K_VERTICAL_P = 3.0
    K_ROLL_P = 50.0
    K_PITCH_P = 30.0

    # Get API URL from controller args (optional)
    try:
        args = robot.getControllerArguments()
        api_url = (args[0] if isinstance(args, (list, tuple)) and args else args or DEFAULT_API) or DEFAULT_API
    except Exception:
        api_url = DEFAULT_API

    target_altitude = 1.0
    poll_counter = 0
    pos_counter = 0
    cmd = None
    api_connected = False
    camera_counter = 0
    
    # Persistent velocity disturbances (updated by velocity commands)
    roll_disturbance = 0.0
    pitch_disturbance = 0.0
    yaw_disturbance = 0.0
    
    # Flying state - track whether drone should be flying
    # Start in hover mode at 1.0m altitude
    is_flying = True
    print("[mavic_api] 🚁 Starting in hover mode at 1.0m altitude")
    
    print(f"[mavic_api] Polling API at {api_url}/mavic/command")

    while robot.step(timestep) != -1:
        t = robot.getTime()
        poll_counter += 1

        # Poll API every timestep (~8ms) for immediate response
        if poll_counter >= 1:
            poll_counter = 0
            cmd = fetch_command(api_url)
            if cmd and not api_connected:
                api_connected = True
                print("[mavic_api] Connected to Rescue Command Center API")
            if cmd:
                cmd_type = cmd.get("type")
                flying = cmd.get("flying", False)
                
                # Process action commands (takeoff, land, hover)
                if cmd_type == "action":
                    action = cmd.get("data", {}).get("action", "")
                    print(f"[mavic_api] ⚡ ACTION command: {action}, flying={flying}")
                    
                    if action == "takeoff":
                        target_altitude = max(target_altitude, 1.0)  # Takeoff to at least 1m
                        is_flying = True
                        print(f"[mavic_api] 🚁 Taking off to {target_altitude:.2f}m")
                    elif action == "land":
                        target_altitude = 0.0  # Land on ground
                        is_flying = False  # Stop flying when landing
                        # Reset disturbances when landing
                        pitch_disturbance = 0.0
                        roll_disturbance = 0.0
                        yaw_disturbance = 0.0
                        print(f"[mavic_api] 🛬 Landing - target altitude: {target_altitude:.2f}m, motors will stop")
                    elif action == "hover":
                        # Maintain current altitude, reset disturbances
                        is_flying = True
                        pitch_disturbance = 0.0
                        roll_disturbance = 0.0
                        yaw_disturbance = 0.0
                        print(f"[mavic_api] 🚁 Hovering at {target_altitude:.2f}m")
                    
                # Update altitude from API if flying
                if flying:
                    new_altitude = cmd.get("target_altitude", target_altitude)
                    if new_altitude != target_altitude:
                        print(f"[mavic_api] 📏 Altitude change: {target_altitude:.2f}m → {new_altitude:.2f}m")
                    target_altitude = new_altitude
                    
                # Process velocity commands
                data = cmd.get("data", {})
                if cmd_type == "velocity":
                    pitch_disturbance = data.get("pitch", 0)
                    roll_disturbance = data.get("roll", 0)
                    yaw_disturbance = data.get("yaw", 0)
                    vertical = data.get("vertical", 0)
                    if pitch_disturbance != 0 or roll_disturbance != 0 or yaw_disturbance != 0 or vertical != 0:
                        print(f"[mavic_api] 🚁 VELOCITY command: pitch={pitch_disturbance:.2f}, roll={roll_disturbance:.2f}, yaw={yaw_disturbance:.2f}, vertical={vertical:.2f}")
                    target_altitude = target_altitude + 0.02 * vertical
                    target_altitude = max(0.0, min(50.0, target_altitude))


        roll, pitch, _ = imu.getRollPitchYaw()
        gps_vals = gps.getValues()
        altitude = gps_vals[2]
        roll_vel, pitch_vel, _ = gyro.getValues()

        # Send position to backend for UI (~4 times/sec)
        pos_counter += 1
        if pos_counter >= 31:  # ~250ms at 8ms timestep
            pos_counter = 0
            send_position(api_url, gps_vals[0], gps_vals[1], gps_vals[2])

        front_left_led.set(int(t) % 2)
        front_right_led.set(1 - int(t) % 2)

        # Send camera frame periodically
        if camera:
            camera_counter += 1
            if camera_counter * timestep >= CAMERA_SAMPLE_PERIOD_MS:
                camera_counter = 0
                # getImage() returns BGRA format as bytes
                img_bgra = camera.getImage()
                if img_bgra:
                    w, h = camera.getWidth(), camera.getHeight()
                    
                    # More efficient BGRA to RGB conversion
                    # Webots Python API returns bytes directly
                    # We need to drop every 4th byte (Alpha) and swap B and R? 
                    # Actually Webots returns BGRA, PIL can read BGRA directly if we pass it correctly
                    # But the backend expects RGB or BGRA based on size.
                    # Let's send the raw BGRA data and let the backend handle it!
                    # The backend router handles len(body) == width * height * 4 as BGRA.
                    
                    # BUT: The backend router says:
                    # if len(body_bytes) == expected_bgra: img = Image.frombytes("BGRA", ...)
                    # So we can just send the raw img_bgra bytes!
                    
                    send_camera_frame(api_url, img_bgra, w, h)

        # Camera roll/pitch limits: roll [-0.5, 0.5], pitch [-0.5, 1.7] per proto
        camera_roll.setPosition(max(-0.5, min(0.5, -0.115 * roll_vel)))
        camera_pitch.setPosition(max(-0.5, min(1.7, -0.1 * pitch_vel)))

        def clamp(v, lo, hi):
            return max(lo, min(hi, v))

        roll_in = K_ROLL_P * clamp(roll, -1, 1) + roll_vel + roll_disturbance
        pitch_in = K_PITCH_P * clamp(pitch, -1, 1) + pitch_vel + pitch_disturbance
        yaw_in = yaw_disturbance
        alt_diff = clamp(target_altitude - altitude + K_VERTICAL_OFFSET, -1, 1)
        vertical_in = K_VERTICAL_P * (alt_diff ** 3)

        # Only apply motor control if flying, otherwise stop motors
        if is_flying or altitude > 0.05:  # Keep flying if above 5cm or explicitly flying
            fl = K_VERTICAL_THRUST + vertical_in - roll_in + pitch_in - yaw_in
            fr = K_VERTICAL_THRUST + vertical_in + roll_in + pitch_in + yaw_in
            rl = K_VERTICAL_THRUST + vertical_in - roll_in - pitch_in + yaw_in
            rr = K_VERTICAL_THRUST + vertical_in + roll_in - pitch_in - yaw_in
        else:
            # Landed - stop all motors
            fl = fr = rl = rr = 0.0

        front_left.setVelocity(fl)
        front_right.setVelocity(-fr)
        rear_left.setVelocity(-rl)
        rear_right.setVelocity(rr)


if __name__ == "__main__":
    main()

