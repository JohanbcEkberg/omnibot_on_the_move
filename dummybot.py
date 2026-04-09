# general
import sys
from time import time, sleep

#from omnibot.tcp import Connection
from tcp import Connection

def run_dummybot(HOST, PORT, verbose=False):
    """
    Runs a dummybot at host HOST that rotates a bit while printing x and y coordinates.
    """
    
    ts = 0.1 # sampling time
    tstart = time()

    with Connection(HOST,PORT,verbose=verbose) as bot:
        print("Connected")
        
        # Target speed for servos
        vset = 100

        # Go one way
        """while time() < tstart + 3:
            t0 = time()

            bot.set_speeds([vset,vset,vset])
              
            print('theta:'+str(bot.get_theta()))
        """
        # Go the other way
        while True:
            import math
            deg_theta = bot.get_theta()
            rad_theta = math.radians(deg_theta)

            bot.set_speeds([vset,vset,vset])
            x = bot.get_x() - 0.12 * math.sin(rad_theta)
            y = bot.get_y() + 0.12 * math.cos(rad_theta)
            print('deg_theta:' + str(deg_theta) + '  rad_theta:' + str(rad_theta) + '  x:'+str(x) + '  y:'+str(y))
            
            sleep(1)
                    
if __name__ == '__main__':
    # Server settings
    HOST = "130.235.83.171"
    PORT = 9004

    if len(sys.argv) > 2:
        # If an input is given to the script, it will be interpreted as the intended
        # IP-address and port. Baseline is localhost, 9998.
        HOST = sys.argv[1]
        PORT = sys.argv[2]
    
    print(f"HOST: \t {HOST}")
    run_dummybot(HOST,PORT)