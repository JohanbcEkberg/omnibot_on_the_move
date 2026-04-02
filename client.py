import requests
import json
from shared import Obstacle, Circle, Box, Triangle

BASE_URL = "http://130.235.83.115:80"

def pretty(resp):
  print(f"Status: {resp.status_code}")
  try:
    print(json.dumps(resp.json(), indent=2))
  except Exception:
    print(resp.text)
  print("-" * 60)

def clearOsb():
  requests.post(f"{BASE_URL}/clearObs")

def update_limits():
  print("POST /updateLimits (with maxvel, maxacc, maxjerk)")

  data = {
    "limits": [
      [-4.0, 4.0],
      [-4.0, 4.0],
      [-3.14159, 3.14159]
    ],
    "maxvel": [1.0, 1.0, 1.0],
    "maxacc": [1.5, 1.5, 1.5],
    "maxjerk": [3.0, 3.0, 3.0]
  }

  resp = requests.post(f"{BASE_URL}/updateJointLimits", json=data)
  pretty(resp)

def info():
  print("GET /info ")
  resp = requests.get(f"{BASE_URL}/info")
  pretty(resp)

def set_obs(obs: list[Obstacle]):
  print("POST /setObs")

  json_obs = []
  for o in obs:
    if isinstance(o, Circle):
      json_obs.append({
        "obstacle_id": o.obstacle_id,
        "type": 0,
        "pos": o.pos,
        "dim": o.dim
      })
    elif isinstance(o, Box):
      json_obs.append({
        "obstacle_id": o.obstacle_id,
        "type": 1,
        "pos": o.pos,
        "dim": o.dim
      })
    elif isinstance(o, Triangle):
      json_obs.append({
        "obstacle_id": o.obstacle_id,
        "type": 2,
        "pos": o.pos,
        "dim": o.dim
      })

  data = {
    "obstacles": json_obs
  }

  resp = requests.post(f"{BASE_URL}/setObs", json=data)
  pretty(resp)

def calc_trajectory(start: list[float], end: list[float]):
  data = {
    "start": start,
    "end": end
  }

  resp = requests.post(f"{BASE_URL}/calcTrajectory", json=data)

  print(f"Status: {resp.status_code}")

  if resp.status_code == 200:
    result = resp.json()
    n = len(result.get("q", []))
    print(f"Trajectory points: {n}")
    print(f"Final time: {result['t'][-1]:.4f}")
    print("-" * 60)
    return result
  else:
    print("Error:", resp.text)

def post_obstacles_to_server(start: list[float], end: list[float], obs: list[Obstacle], clear_first: bool = True):
  if clear_first:
    clearOsb()
  #info()

  set_obs(obs)

  if len(start) == 2:
    start = [start[0], start[1], 0.0]
  if len(end) == 2:
    end = [end[0], end[1], 0.0]

  traj = calc_trajectory(start, end )
  with open("traj.json", "w") as f:
    json.dump(traj, f, indent=4)