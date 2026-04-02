from tcp import Connection
import threading

class Omnibot:
  def __init__(self, host: str = "localhost", port: int = 8000):
    self.host = host
    self.port = port
    self.connection = Connection(host, port, verbose=True)
    self.running: threading.Event = threading.Event()
    self.completed_path: threading.Event = threading.Event()

  def start(self):
    if self.running.is_set():
      print("Omnibot server is already running.")
      return
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
  
  def control_loop(self):
    while True:
      print("Waiting for control loop to start...")
      self.running.wait()
      print("TODO: Implement control_loop()")
      print("Running control loop...")

      import time
      time.sleep(0.3)
      print("Control loop completed.")