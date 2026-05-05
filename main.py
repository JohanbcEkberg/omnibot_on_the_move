import json
import requests

from gui import create_gui
from omnibot import Omnibot
import threading

HOST = "130.235.83.171"
SERVER_URL = "http://130.235.83.115:80"
PORT = 9003

MIN_Y = -1.5
MAX_Y = 1.5
MIN_X = -2.0
MAX_X = 2.0

if __name__ == "__main__":
  data = {
    "limits": [
      [MIN_X, MAX_X],
      [MIN_Y, MAX_Y],
      [-3.14159, 3.14159]
    ],
    "maxvel": [1.0, 1.0, 1.0],
    "maxacc": [1.5, 1.5, 1.5],
    "maxjerk": [3.0, 3.0, 3.0]
  }

  resp = requests.post(f"{SERVER_URL}/updateJointLimits", json=data)
  print(f"Status: {resp.status_code}")
  try:
    print(json.dumps(resp.json(), indent=2))
  except Exception:
    print(resp.text)

  bot = Omnibot(HOST, PORT)
  threading.Thread(target=bot.control_loop, daemon=True).start()
  gui = create_gui(bot)