import socket
        
class Connection(object):
    """A class that implements a servo-client which is capable of sending servo speed-settings
    to an omnibot. 

    HOST: Host name of server (string)
    PORT: Port to connect to (int) 
    verbose: choose level of chit-chat (boolean)
    """
    def __init__(self,HOST,PORT,verbose=False):
        self.HOST = HOST
        self.PORT = PORT
        self.verbose=verbose
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def __enter__(self):
        """Boot up the socket and connect to the omnibot server
        """
        if self.verbose:
            print("Connecting to HOST: " + str(self.HOST) + ", PORT: " + str(self.PORT))

        self.sock.connect((self.HOST, self.PORT)) # Connect to the robot
        if self.verbose:
            print("Connection successful.")


        return self
    
    def __exit__(self, exc_type, exc_value, exc_tb):
        """Close down the socket after closing the client
        """
        if self.verbose:
            print("Closing down socket")
        self.sock.close()

    def _send_and_receive(self,message):
        """Send a message (string) to the omnibot and return the answer (string) that the omnibot gave.

        Message format (string):
            "abc"
            a: w or r, signifying write to servo or read from crazyflie
            b: if a=w, b is the vector index of the servo to write to. If a=r, b is the type of information to read
            c: if a=w, c is the speed to be written.

        Examples of message format:
            w110, "write speed 10 to servo of vector index 1"
            rx, "read x coordinate"
        """
        # Send the package                      
        self.sock.sendall(bytes(message,'utf-8'))
        # Receive confirmation
        ret=self.sock.recv(1024).decode('utf-8')

        # Remove the end of the line to account for newline, which is required for julia socket implementation.
        return ret[:-1]

    def set_speed(self,i,v):
        """Set the speed of servo i (int) to v (int). Return a string with status of the operation from the omnibot.
        i can take values 0, 1 or 2, and it should be tested which of these values maps to which servo.
        """

        package = 'w'+str(i)+str(v)
        if self.verbose:
            print("Sending " + package)


        ret = self._send_and_receive(package)

        if ret[0] == "e":
            raise Exception(ret)
        elif self.verbose:
            print(ret)
        return ret

    def set_speeds(self,v):
        """Set the speed of the servos to the values in vector v (ints).
        """
        for (i,vi) in enumerate(v):
            self.set_speed(i,vi)

    def get_x(self):
        """Get x coordinate as float
        """
        if self.verbose:
            print("Requesting x")                 

        ret = self._send_and_receive("rx")
        if ret[0] == "e":
            raise Exception(ret)

        if self.verbose:
            print("x: "+ret)

        return float(ret)

    def get_y(self):
        """Get y coordinate as float
        """
        if self.verbose:
            print("Requesting y")                 

        ret = self._send_and_receive("ry")
        if ret[0] == "e":
            raise Exception(ret)

        if self.verbose:
            print("y: "+ret)

        return float(ret)
        
    def get_z(self):
        """Get z coordinate as float
        """
        if self.verbose:
            print("Requesting z")                 

        ret = self._send_and_receive("rz")
        if ret[0] == "e":
            raise Exception(ret)

        if self.verbose:
            print("z: "+ret)

        return float(ret)

    def get_theta(self):
        """Get angle theta as float
        """
        if self.verbose:
            print("Requesting theta")                 

        ret = self._send_and_receive("rtheta")
        if ret[0] == "e":
            raise Exception(ret)

        if self.verbose:
            print("theta: "+ret)

        return float(ret)


    def get_state(self):
        """"Get state vector of [x y theta]^T."""

        x = self.get_x()
        y = self.get_y()
        theta = self.get_theta()

        return [x,y,theta]

    def get_max_speed(self):
        """"Get maximum speed-setpoint for servos."""

        if self.verbose:
            print("Requesting theta")                 

        ret = self._send_and_receive("rmaxspeed")
        if ret[0] == "e":
            raise Exception(ret)

        if self.verbose:
            print("max speed: "+ret)

        return int(ret)
