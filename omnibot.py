from tcp import Connection
import threading
from collections import deque
import time
import math
import json

MAX_SPEED = 1022
MIN_SPEED = -1022

WHEEL_TO_CENTER_DIST = 0.12

TWO_PI_OVER_3 = 2 * math.pi / 3
FOUR_PI_OVER_3 = 4 * math.pi / 3

MOTOR_SCALING_FACTOR = 1

class Omnibot:
  def __init__(self, host: str = "localhost", port: int = 8000):
    self.host = host
    self.port = port
    self.connection = Connection(host, port, verbose=False)
    self.running = threading.Event()
    self.completed_path = threading.Event()
    self.positions = []      # [[x, y, theta], ...]
    self.velocities = []     # [[vx, vy, vtheta], ...]
    self.accelerations = []    # [[ax, ay, atheta], ...]
    self.r = 0.02
    self.r_denom = 1 / self.r
    self.R = 0.15

  def start(self):
    if self.running.is_set():
      print("Omnibot server is already running.")
      return

    if len(self.positions) == 0 or len(self.velocities) == 0 or len(self.accelerations) == 0:
      print("Reading trajectory data from traj.json...")
      with open("traj.json", "r") as f:
        import json
        traj = json.load(f)
        self.positions = traj.get("q", [])
        self.velocities = traj.get("q_dot", [])
        self.accelerations = traj.get("q_dot_dot", [])

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

  def clamp(self, value, min_value, max_value):
    return max(min(value, max_value), min_value)

  def normalize_angle_rad(self, angle_rad):
    """Normalize angle to [-pi, pi] radians."""
    while angle_rad > math.pi:
      angle_rad -= 2 * math.pi
    while angle_rad < -math.pi:
      angle_rad += 2 * math.pi
    return angle_rad

  def _calc_wheel_speeds(self, v_vector, theta):
    """
    Implements the mathematical mapping from Equation 1.
    v_vector: [vx, vy, vtheta]
    theta: current orientation in radians
    """
    vx, vy, vtheta = v_vector
    
    phi1 = (-math.sin(theta) * vx + math.cos(theta) * vy + self.R * vtheta) * self.r_denom
    phi2 = (-math.sin(theta + TWO_PI_OVER_3) * vx + math.cos(theta + TWO_PI_OVER_3) * vy + self.R * vtheta) * self.r_denom
    phi3 = (-math.sin(theta + FOUR_PI_OVER_3) * vx + math.cos(theta + FOUR_PI_OVER_3) * vy + self.R * vtheta) * self.r_denom

    return [phi1, phi2, phi3]
  
  def control_loop(self):
    K = 6
    D = 1.5
    I = 1
    theta_scale = 0.25
    theta_cmd_limit = 2.6
    feedforward_gain = 0.95
    derivative_alpha = 0.7

    prev_error_x = 0.0
    prev_error_y = 0.0
    prev_error_theta = 0.0
    
    
    int_error_x = 0.0
    int_error_y = 0.0
    int_error_theta = 0.0

    dt_target = 0.01

    filt_derivative_x = 0.0
    filt_derivative_y = 0.0
    filt_derivative_theta = 0.0
    
    filt_theta = 0.0

    time_index = 0
    last_tick = time.monotonic()

    skipped = 0
    used = 0
    moving_average = deque(maxlen=5)
    
    log = {"q" : []}
    with self.connection as conn:
      last_state = conn.get_state()
      last_sample = last_state
      while True:
        while not self.running.is_set():
          self.running.wait()
          last_tick = time.monotonic()
        if time_index >= len(self.positions) or time_index >= len(self.velocities):
          break

        now = time.monotonic()
        dt = now - last_tick
        last_tick = now
        dt = max(dt, dt_target)
        div_dt = 1 / dt
        
        current_state = conn.get_state() # [x, y, theta]
        current_state[2] = math.radians(current_state[2]) # Convert theta to radians
        current_state[0] -= WHEEL_TO_CENTER_DIST * math.sin(current_state[2])
        current_state[1] += WHEEL_TO_CENTER_DIST * math.cos(current_state[2])

        ref_pos = self.positions[time_index]
        ref_vel = self.velocities[time_index]

        state_diff = [current_state[i] - last_state[i] for i in range(2)]
        ref_diff = [ref_pos[i] - last_sample[i] for i in range(2)]
        time_index += 1

        dot_product = state_diff[0] * ref_diff[0] + state_diff[1] * ref_diff[1]
        if dot_product < 0:
          skipped += 1
          print(f"Warning: Robot seems to be moving away from the reference trajectory at index {time_index}. Skipping this point.")
          last_sample = ref_pos
          last_state = current_state
          elapsed = time.monotonic() - now
          time.sleep(max(0.0, dt_target - elapsed))
          continue
        used += 1
        

        error_x = ref_pos[0] - current_state[0]
        error_y = ref_pos[1] - current_state[1]
        error_theta = self.normalize_angle_rad(ref_pos[2] - current_state[2])
        
        int_error_x += error_x * dt
        int_error_y += error_y * dt
        int_error_theta += error_theta *dt

        x_derivative = (error_x - prev_error_x) * div_dt
        y_derivative = (error_y - prev_error_y) * div_dt
        theta_derivative = (error_theta - prev_error_theta) * div_dt

        filt_derivative_x = derivative_alpha * filt_derivative_x + (1.0 - derivative_alpha) * x_derivative
        filt_derivative_y = derivative_alpha * filt_derivative_y + (1.0 - derivative_alpha) * y_derivative
        filt_derivative_theta = derivative_alpha * filt_derivative_theta + (1.0 - derivative_alpha) * theta_derivative

        vx_cmd = K * error_x + D * filt_derivative_x + I * int_error_x
        vy_cmd = K * error_y + D * filt_derivative_y + I * int_error_y
        vtheta_cmd = K * error_theta + D * filt_derivative_theta + I * int_error_theta

        vx_cmd = feedforward_gain * ref_vel[0] + vx_cmd
        vy_cmd = feedforward_gain * ref_vel[1] + vy_cmd
        vtheta_cmd = feedforward_gain * ref_vel[2] + vtheta_cmd
        vtheta_cmd = self.clamp(vtheta_cmd * theta_scale, -theta_cmd_limit, theta_cmd_limit)

        prev_error_x = error_x
        prev_error_y = error_y
        prev_error_theta = error_theta
        
        moving_average.append([vx_cmd, vy_cmd, vtheta_cmd])
        x_average = 0
        y_average = 0
        theta_average = 0
        
        for x, y, theta in moving_average:
          x_average += x
          y_average += y
          theta_average += theta
          
        
        phi = self._calc_wheel_speeds([x_average / 5, y_average / 5, theta / 5], current_state[2])
        # phi = self._calc_wheel_speeds([vx_cmd, vy_cmd, vtheta_cmd], current_state[2])

        int_phi = [self.clamp(int(p * MOTOR_SCALING_FACTOR), MIN_SPEED, MAX_SPEED) for p in phi]

        conn.set_speeds([0] + int_phi)
        print(f"Current state: {current_state}, Wheel speeds: {int_phi}")
        log["q"].append(current_state)

        elapsed = time.monotonic() - now
        last_sample = ref_pos
        last_state = current_state
        time.sleep(max(0.0, dt_target - elapsed))
      # End while loop (stupid mf python makes it hard to see) womp womp johan
      conn.set_speeds([0, 0, 0, 0])
    print("Control loop finished.")
    print(f"Skipped {skipped} points, used {used} points.")
    self.mark_done()
    
    with open("actual_traj.json", "w") as f:
      json.dump(log, f, indent=2)