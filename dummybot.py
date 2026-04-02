# general
import sys
from time import time, sleep

#from omnibot.tcp import Connection
from tcp import Connection

def run_dummybot(HOST, PORT, verbose=True):
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
            t0 = time()
            print('x:'+str(bot.get_x()) + '  y:'+str(bot.get_y()) )
            #bot.set_speeds([-vset,-vset,-vset])
              
            print('theta:'+str(bot.get_theta()))
            
            sleep(max(0,t0+ts-time()+10))
                    
if __name__ == '__main__':
    # Server settings
    HOST = "130.235.83.171"
    PORT = 9005

    if len(sys.argv) > 2:
        # If an input is given to the script, it will be interpreted as the intended
        # IP-address and port. Baseline is localhost, 9998.
        HOST = sys.argv[1]
        PORT = sys.argv[2]
    
    print(f"HOST: \t {HOST}")
    run_dummybot(HOST,PORT)