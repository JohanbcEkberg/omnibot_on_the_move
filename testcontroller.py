# general
import numpy as np
import sys
from time import time, sleep

# threads
import threading

# Controller
from inputs import get_gamepad

from .tcp import Connection

class ControllerState:
    """
    Class that logs the controller state
    """
    def __init__(self):
        """ Initialize the controller """
        self.x = 128
        self.y = 128
        self.r = 128
        self.on = True
        
    def set_x(self,x):
        self.x = x
    def set_y(self,y):
        self.y = y
    def set_r(self,r):
        self.r = r
    def state_data(self):
        return 'x'+str(self.x)+'y'+str(self.y)+'r'+str(self.r)
    def set_state(self,data):
        s = str(data)
        ind = [s.find(i) for i in ['x','y','r']]
        self.set_x(int(s[ind[0]+1:ind[1]]))
        self.set_y(int(s[ind[1]+1:ind[2]]))
        self.set_r(int(s[ind[2]+1:-1]))
        
def log_controller(state):
    """
    Function that continuously listens to any event from the controller, and logs the change in
    the controller state "state"
    """
    while 1:
        events = get_gamepad()
        for event in events:
            if event.code == "ABS_X":
                state.set_x(event.state)
            elif event.code == "ABS_Y":
                state.set_y(event.state)
            elif event.code == "ABS_Z":
                state.set_r(event.state)
            elif event.code == "BTN_PINKIE" and event.state == 1:
                # The "BTN_PINKIE" (right index trigger) 
                # is currently used as an off-button.
                state.on = False



def run_omnibot_with_controller(HOST,verbose=False):
    """
    Connect to an omnibot at ip HOST and proceed to steer it with a controller and print current position of omnibot.
    """
    
    # Robot parameters
    R = 0.16 		# Distance between center of robot and wheels
    a1 = 2*np.pi/3 	# Angle between x axis and first wheel
    a2 = 4*np.pi/3  # Angle between x axis and second wheel
    r = 0.028*0.45/18 # Wheel radius. Has been fudge-factored because the actual velocity of the wheels did not align with the set-points.

    
    vel_factor = 6 # Fudge factor that changes the relative velocity of the bot
    
    def phidot(xdot,ang):
        """Returns reference velocities for the wheels, given current system state and reference velocities"""
        M = -1/r*np.array([[-np.sin(ang), np.cos(ang), R ],[-np.sin(ang+a1), np.cos(ang+a1), R],[-np.sin(ang+a2), np.cos(ang+a2), R]])
        return M.dot(xdot) 
    
    # Start loggin controller
    state = ControllerState()
    t = threading.Thread(target=log_controller, args=(state,), daemon=True)
    t.start()
    
    ts = 0.1 # sampling time
    
    with Connection(HOST,verbose=verbose) as bot:
        while state.on:
            t0 = time()

            # Get gamepad updates.
            # Use some scaling to turn the controller state values into
            # reasonable velocities.
            w = (128-state.r)*np.pi/1000
            vy = (128-state.x)/1500
            vx = (128-state.y)/1500
            dphi = vel_factor*phidot([vx,vy,w],0.0)
            
            for i,v in enumerate(dphi):
                bot.set_speed(i,round(v))
                    
            print('x:'+str(bot.get_x()))
            print('y:'+str(bot.get_y()))

            sleep(max(0,t0+ts-time()))
                    

if __name__ == '__main__':

    # Server settings
    HOST = "localhost"

    if len(sys.argv) > 1:
        # If an input is given to the script, it will be interpreted as the intended
        # IP-address. Baseline is localhost.
        HOST = sys.argv[1]
    
    print(f"HOST: \t {HOST}")
    run_omnibot_with_controller(HOST)