from tcp import Connection
import threading
import time
import math

class Omnibot:
  def __init__(self, host: str = "localhost", port: int = 8000):
    self.host = host
    self.port = port
    self.connection = Connection(host, port, verbose=True)
    self.running: threading.Event = threading.Event()
    self.completed_path: threading.Event = threading.Event()
    self.positions = []
    self.velocities = []
    self.accelerations = []
    self.r = 0.025
    self.R = 0.15
    self.state = [1, 0, 0] # x, y, theta

  def start(self):
    if self.running.is_set():
      print("Omnibot server is already running.")
      return

    # if len(self.positions) == 0 or len(self.velocities) == 0 or len(self.accelerations) == 0:
    #   print("Reading trajectory data from traj.json...")
    #   with open("traj.json", "r") as f:
    #     import json
    #     traj = json.load(f)
    #     self.positions = traj.get("q", [])
    #     self.velocities = traj.get("q_dot", [])
    #     self.accelerations = traj.get("q_dot_dot", [])

    self.completed_path.clear()
    self.running.set()

  def stop(self):
    if not self.running.is_set():
      print("Omnibot server is not running.")
      return
    self.running.clear()
    
  def done(self) -> bool:
    return self.completed_path.is_set()

  def mark_done(self):
    self.completed_path.set()
    self.running.clear()

  def _calc_velocities(self, state, degrees):
    print(f"Calculating wheel speeds for state: {state} and orientation: {degrees} degrees")
    vx, vy, vtheta = state
    theta = math.radians(degrees)

    phi1 = (-math.sin(theta) * vx + math.cos(theta) * vy + self.R * vtheta) / self.r
    phi2 = (-math.sin(theta + 2*math.pi/3) * vx + math.cos(theta + 2*math.pi/3) * vy + self.R * vtheta) / self.r
    phi3 = (-math.sin(theta + 4*math.pi/3) * vx + math.cos(theta + 4*math.pi/3) * vy + self.R * vtheta) / self.r

    return [phi1, phi2, phi3]
  
  def control_loop(self):
    K_p = 4.0
    dt = 0.05
    
    target_vx = 5
    target_vy = 0.0
    target_vtheta = 0.0

    with self.connection as conn:
        while True:
            while not self.running.is_set():
              self.running.wait()

            robot_state = conn.get_state()
            print(f"Current robot state: {robot_state}")
            current_theta = robot_state[2]

            error_y = 0.0 - robot_state[1]
            error_theta = 0.0 - robot_state[2]

            vx_cmd = target_vx
            vy_cmd = target_vy + K_p * error_y
            vtheta_cmd = target_vtheta + K_p * error_theta

            phi = self._calc_velocities([vx_cmd, 0, 0], current_theta)

            int_phi = [min(max(int(p), -1022), 1022) for p in phi]

            print(f"Calculated wheel speeds: {int_phi}")

            conn.set_speeds(int_phi)
            time.sleep(dt)