"""Enhanced LPG fire supervisor controller with centralized robot control."""

import json
import urllib.request
import urllib.error
import math
from controller import Supervisor

DEFAULT_API = "http://127.0.0.1:8000"
TIME_STEP = 32


class RobotController:
    """Centralized controller for all robots using Supervisor API."""
    
    def __init__(self, supervisor):
        self.supervisor = supervisor
        self.timestep = TIME_STEP
        
        print("[Supervisor] Initializing robot controller...")
        
        # Get robot nodes by DEF name (Added in .wbt)
        self.mavic = self.supervisor.getFromDef("MAVIC")
        self.tiago1 = self.supervisor.getFromDef("TIAGO1")
        self.tiago2 = self.supervisor.getFromDef("TIAGO2")
        self.tiago3 = self.supervisor.getFromDef("TIAGO3")
        
        print(f"[Supervisor] ✓ Mavic found: {self.mavic is not None}")
        print(f"[Supervisor] ✓ Tiago 1 found: {self.tiago1 is not None}")
        print(f"[Supervisor] ✓ Tiago 2 found: {self.tiago2 is not None}")
        print(f"[Supervisor] ✓ Tiago 3 found: {self.tiago3 is not None}")
    
    def _get_robot(self, target):
        """Get robot node by target name."""
        if target == "mavic":
            return self.mavic
        elif target == "tiago1":
            return self.tiago1
        elif target == "tiago2":
            return self.tiago2
        elif target == "tiago3":
            return self.tiago3
        return None
    
    # ========== COMMAND PROCESSING ==========
    
    def process_command(self, cmd):
        """Process a command from the API."""
        if not cmd or cmd.get("type") == "none":
            return
        
        cmd_type = cmd.get("type")
        target = cmd.get("target")
        data = cmd.get("data", {})
        
        try:
            if cmd_type == "teleport":
                self._handle_teleport(target, data)
            elif cmd_type == "velocity":
                self._handle_velocity(target, data)
            elif cmd_type == "stop":
                self._handle_stop(target)
            elif cmd_type == "stop_all":
                self._handle_stop_all()
            elif cmd_type == "rotate":
                self._handle_rotate(target, data)
            elif cmd_type == "formation":
                self._handle_formation(data)
            elif cmd_type == "multi_command":
                self._handle_multi_command(data)
            elif cmd_type == "mavic_land":
                self._handle_mavic_land()
            elif cmd_type == "get_position":
                self._handle_get_position(target)
            elif cmd_type == "get_all_status":
                self._handle_get_all_status()
            else:
                print(f"[Supervisor] ⚠ Unknown command type: {cmd_type}")
        except Exception as e:
            print(f"[Supervisor] ❌ Error processing command: {e}")
    
    def _handle_teleport(self, target, data):
        """Handle teleport command."""
        robot = self._get_robot(target)
        if not robot:
            print(f"[Supervisor] ⚠ Robot not found: {target}")
            return
        
        x, y, z = data.get("x", 0), data.get("y", 0), data.get("z", 0)
        translation_field = robot.getField("translation")
        translation_field.setSFVec3f([x, y, z])
        print(f"[Supervisor] 📍 Teleported {target} to ({x:.2f}, {y:.2f}, {z:.2f})")
    
    def _handle_velocity(self, target, data):
        """Handle velocity command."""
        robot = self._get_robot(target)
        if not robot:
            print(f"[Supervisor] ⚠ Robot not found: {target}")
            return
        
        vx = data.get("vx", 0)
        vy = data.get("vy", 0)
        vz = data.get("vz", 0)
        wx = data.get("wx", 0)
        wy = data.get("wy", 0)
        wz = data.get("wz", 0)
        
        robot.setVelocity([vx, vy, vz, wx, wy, wz])
        print(f"[Supervisor] 🚀 Set {target} velocity: v=({vx:.2f}, {vy:.2f}, {vz:.2f}), w=({wx:.2f}, {wy:.2f}, {wz:.2f})")
    
    def _handle_stop(self, target):
        """Handle stop command."""
        robot = self._get_robot(target)
        if not robot:
            print(f"[Supervisor] ⚠ Robot not found: {target}")
            return
        
        robot.resetPhysics()
        print(f"[Supervisor] 🛑 Stopped {target}")
    
    def _handle_stop_all(self):
        """Handle stop all command."""
        for robot in [self.mavic, self.tiago1, self.tiago2, self.tiago3]:
            if robot:
                robot.resetPhysics()
        print("[Supervisor] 🛑 Stopped all robots")
    
    def _handle_rotate(self, target, data):
        """Handle rotation command."""
        robot = self._get_robot(target)
        if not robot:
            print(f"[Supervisor] ⚠ Robot not found: {target}")
            return
        
        axis_x = data.get("axis_x", 0)
        axis_y = data.get("axis_y", 0)
        axis_z = data.get("axis_z", 1)
        angle = data.get("angle", 0)
        
        rotation_field = robot.getField("rotation")
        rotation_field.setSFRotation([axis_x, axis_y, axis_z, angle])
        print(f"[Supervisor] 🔄 Rotated {target}: axis=({axis_x}, {axis_y}, {axis_z}), angle={angle:.2f}")
    
    def _handle_formation(self, data):
        """Handle formation command."""
        formation_type = data.get("formation_type", "line")
        center_x = data.get("center_x", 0)
        center_y = data.get("center_y", 0)
        z = data.get("z", 0.095)
        spacing = data.get("spacing", 1.5)
        
        if formation_type == "line":
            self._formation_line(center_x, center_y, z, spacing)
        elif formation_type == "triangle":
            self._formation_triangle(center_x, center_y, z, spacing)
        elif formation_type == "square":
            self._formation_square(center_x, center_y, z, spacing)
        elif formation_type == "circle":
            self._formation_circle(center_x, center_y, z, spacing)
        else:
            print(f"[Supervisor] ⚠ Unknown formation type: {formation_type}")
    
    def _formation_line(self, start_x, start_y, z, spacing):
        """Arrange Tiagos in a line."""
        positions = [
            (start_x, start_y, z),
            (start_x + spacing, start_y, z),
            (start_x + 2*spacing, start_y, z)
        ]
        for i, (tiago, pos) in enumerate(zip([self.tiago1, self.tiago2, self.tiago3], positions), 1):
            if tiago:
                translation_field = tiago.getField("translation")
                translation_field.setSFVec3f(list(pos))
        print(f"[Supervisor] 🎯 Tiagos arranged in LINE at ({start_x}, {start_y}), spacing={spacing}")
    
    def _formation_triangle(self, center_x, center_y, z, radius):
        """Arrange Tiagos in a triangle."""
        positions = [
            (center_x + radius * math.cos(0), center_y + radius * math.sin(0), z),
            (center_x + radius * math.cos(2*math.pi/3), center_y + radius * math.sin(2*math.pi/3), z),
            (center_x + radius * math.cos(4*math.pi/3), center_y + radius * math.sin(4*math.pi/3), z)
        ]
        for i, (tiago, pos) in enumerate(zip([self.tiago1, self.tiago2, self.tiago3], positions), 1):
            if tiago:
                translation_field = tiago.getField("translation")
                translation_field.setSFVec3f(list(pos))
        print(f"[Supervisor] 🎯 Tiagos arranged in TRIANGLE at ({center_x}, {center_y}), radius={radius}")
    
    def _formation_square(self, center_x, center_y, z, spacing):
        """Arrange Tiagos in a square (3 corners)."""
        half = spacing / 2
        positions = [
            (center_x - half, center_y - half, z),
            (center_x + half, center_y - half, z),
            (center_x, center_y + half, z)
        ]
        for i, (tiago, pos) in enumerate(zip([self.tiago1, self.tiago2, self.tiago3], positions), 1):
            if tiago:
                translation_field = tiago.getField("translation")
                translation_field.setSFVec3f(list(pos))
        print(f"[Supervisor] 🎯 Tiagos arranged in SQUARE at ({center_x}, {center_y}), spacing={spacing}")
    
    def _formation_circle(self, center_x, center_y, z, radius):
        """Arrange Tiagos in a circle."""
        positions = [
            (center_x + radius * math.cos(i * 2*math.pi/3), 
             center_y + radius * math.sin(i * 2*math.pi/3), z)
            for i in range(3)
        ]
        for i, (tiago, pos) in enumerate(zip([self.tiago1, self.tiago2, self.tiago3], positions), 1):
            if tiago:
                translation_field = tiago.getField("translation")
                translation_field.setSFVec3f(list(pos))
        print(f"[Supervisor] 🎯 Tiagos arranged in CIRCLE at ({center_x}, {center_y}), radius={radius}")
    
    def _handle_multi_command(self, data):
        """Handle multiple commands."""
        commands = data.get("commands", [])
        print(f"[Supervisor] 🎛️ Processing {len(commands)} commands")
        for cmd in commands:
            self.process_command(cmd)
    
    def _handle_mavic_land(self):
        """Handle Mavic land command."""
        if self.mavic:
            # Get current position
            pos = self.mavic.getPosition()
            # Set to ground level
            translation_field = self.mavic.getField("translation")
            translation_field.setSFVec3f([pos[0], pos[1], 0.1])
            # Stop movement
            self.mavic.resetPhysics()
            print("[Supervisor] 🚁 Mavic landing")
    
    def _handle_get_position(self, target):
        """Handle get position query."""
        robot = self._get_robot(target)
        if robot:
            pos = robot.getPosition()
            print(f"[Supervisor] 📍 {target} position: ({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f})")
    
    def _handle_get_all_status(self):
        """Handle get all status query."""
        print("[Supervisor] 📊 All robot status:")
        for name, robot in [("mavic", self.mavic), ("tiago1", self.tiago1), 
                            ("tiago2", self.tiago2), ("tiago3", self.tiago3)]:
            if robot:
                pos = robot.getPosition()
                vel = robot.getVelocity()
                print(f"  {name}: pos=({pos[0]:.2f}, {pos[1]:.2f}, {pos[2]:.2f}), "
                      f"vel=({vel[0]:.2f}, {vel[1]:.2f}, {vel[2]:.2f})")
    
    # ========== AI MISSION EXECUTION ==========
    
    def poll_ai_missions(self):
        """Poll AI coordinator for robot action plans and execute them."""
        for robot_id in ["mavic", "tiago1", "tiago2", "tiago3"]:
            try:
                plan = self._fetch_ai_plan(robot_id)
                if plan and "next_action" in plan:
                    next_action = plan["next_action"]
                    action_type = next_action.get("action")
                    
                    if action_type == "navigate":
                        target = next_action.get("target", {})
                        print(f"[AI Mission] {robot_id} → ({target.get('x'):.2f}, {target.get('y'):.2f})")
                        self._handle_teleport(robot_id, {"position": target})
                        self._report_ai_progress(robot_id, {"step_completed": True, "position": target})
                    
                    elif action_type == "execute_task":
                        description = next_action.get("description", "Task")
                        print(f"[AI Mission] {robot_id}: {description}")
                        self._report_ai_progress(robot_id, {"step_completed": True})
                    
                    elif action_type == "report_complete":
                        print(f"[AI Mission] {robot_id} ✓ Complete")
                        self._report_ai_progress(robot_id, {"step_completed": True})
            except:
                pass
    
    def _fetch_ai_plan(self, robot_id):
        """Fetch AI action plan."""
        try:
            req = urllib.request.Request(f"{DEFAULT_API}/mission/ai/plan/{robot_id}")
            with urllib.request.urlopen(req, timeout=0.5) as resp:
                return json.loads(resp.read().decode())
        except:
            return None
    
    def _report_ai_progress(self, robot_id, status):
        """Report progress to AI."""
        try:
            data = json.dumps(status).encode()
            req = urllib.request.Request(f"{DEFAULT_API}/mission/robot/{robot_id}/status", data=data, method="POST")
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=0.5) as resp:
                pass
        except:
            pass
            
    def _report_all_positions(self):
        """Report positions of all robots to backend (mission API + mavic/tiago for UI)."""
        robots = [
            ("mavic", self.mavic, None),
            ("tiago1", self.tiago1, "1"),
            ("tiago2", self.tiago2, "2"),
            ("tiago3", self.tiago3, "3")
        ]
        
        for robot_id, robot_node, tiago_id in robots:
            if robot_node:
                pos = robot_node.getPosition()
                status = {"position": {"x": pos[0], "y": pos[1], "z": pos[2]}}
                self._report_ai_progress(robot_id, status)
                # Yaw for Tiagos (for move_to driving): extract from 3x3 rotation matrix (world Z)
                yaw = None
                if tiago_id:
                    try:
                        # getOrientation() returns 3x3 row-major: R[0][0]=o[0], R[1][0]=o[3]; yaw = atan2(R[1][0], R[0][0])
                        o = robot_node.getOrientation()
                        if o and len(o) >= 4:
                            yaw = math.atan2(float(o[3]), float(o[0]))
                    except Exception:
                        pass
                self._post_position_to_api(robot_id, tiago_id, pos[0], pos[1], pos[2], yaw)
    
    def _post_position_to_api(self, robot_id, tiago_id, x, y, z, yaw=None):
        """POST position to mavic/position or tiago/{id}/position for UI coordinates bar."""
        try:
            payload = {"x": x, "y": y, "z": z}
            if yaw is not None:
                payload["yaw"] = yaw
            data = json.dumps(payload).encode()
            if robot_id == "mavic":
                url = f"{DEFAULT_API}/mavic/position"
            elif tiago_id:
                url = f"{DEFAULT_API}/tiago/{tiago_id}/position"
            else:
                return
            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=0.3) as resp:
                pass
        except (urllib.error.URLError, OSError):
            pass



def fetch_command(api_url):
    """Fetch command from supervisor API."""
    try:
        req = urllib.request.Request(f"{api_url}/supervisor/command")
        with urllib.request.urlopen(req, timeout=0.5) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, OSError, json.JSONDecodeError):
        return None


def main():
    supervisor = Supervisor()
    controller = RobotController(supervisor)
    
    print("[Supervisor] 🚀 Robot control system started")
    print(f"[Supervisor] Polling API at {DEFAULT_API}/supervisor/command")
    print(f"[Supervisor] AI Mission polling enabled")
    
    api_connected = False
    poll_counter = 0
    ai_mission_counter = 0
    
    AI_MISSION_INTERVAL = 30  # Poll AI missions every ~1 second (30 * 32ms)
    
    # Main control loop
    while supervisor.step(TIME_STEP) != -1:
        poll_counter += 1
        ai_mission_counter += 1
        
        # Poll supervisor API every timestep for direct commands
        if poll_counter >= 1:
            poll_counter = 0
            cmd = fetch_command(DEFAULT_API)
            
            if cmd and not api_connected:
                api_connected = True
                print("[Supervisor] ✓ Connected to API")
            
            if cmd and cmd.get("type") != "none":
                controller.process_command(cmd)
        
        # Poll AI mission coordinator (less frequent)
        if ai_mission_counter >= AI_MISSION_INTERVAL:
            ai_mission_counter = 0
            controller.poll_ai_missions()
            controller._report_all_positions()  # Keep UI updated with real positions


if __name__ == "__main__":
    main()
