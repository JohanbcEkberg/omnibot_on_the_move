from gui import create_gui
from omnibot import Omnibot
import threading

HOST = "130.235.83.171"
PORT = 9005

if __name__ == "__main__":
  bot = Omnibot(HOST, PORT)
  threading.Thread(target=bot.control_loop, daemon=True).start()
  gui = create_gui(bot)