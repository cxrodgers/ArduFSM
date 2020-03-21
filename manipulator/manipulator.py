# Print out the position of the manipulators 

import serial
import time
import numpy as np
import math

with serial.Serial('/dev/ttyUSB0', timeout=0) as ser:
    while True:
        # Request position
        ser.write('POS\r') 
        
        # Wait for response
        time.sleep(.1)
        
        # Print response
        resp = ser.readline()
        
        # Split into X, Y, Z
        # Convert to microns
        xyz = np.array(map(int, resp.split())) * 0.1
        
        print "X=%4.1f Y=%4.1f Z=%4.1f" % (xyz[0], xyz[1], xyz[2])
