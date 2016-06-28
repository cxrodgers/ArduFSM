# Main script to run to run WaitToStart behavior
# This is an example of how to write a protocol that sends parameters
# to the Arduino, then displays a message to the user, then starts
# the behavior once the user presses enter.

import time
import json
import os
import sys
import os
import numpy as np, pandas
import my
import time
import curses
import matplotlib.pyplot as plt
import ArduFSM
from ArduFSM import TrialSpeak, TrialMatrix
from ArduFSM import trial_setter_ui
from ArduFSM import Scheduler
from ArduFSM import trial_setter
from ArduFSM import mainloop
import ParamsTable
import shutil


# Check the serial port exists
if not os.path.exists(runner_params['serial_port']):
    raise OSError("serial port %s does not exist" % 
        runner_params['serial_port'])

## Create Chatter
logfilename = None # autodate
chatter = ArduFSM.chat.Chatter(to_user=logfilename, to_user_dir='./logfiles',
    baud_rate=115200, serial_timeout=.1, 
    serial_port=runner_params['serial_port'])
logfilename = chatter.ofi.name

## Initialize UI

# Set the parameters
cmd = TrialSpeak.command_set_parameter('VAR0', 100) 
self.chatter.queued_write_to_device(cmd)
cmd = TrialSpeak.command_set_parameter('VAR1', 200) 
self.chatter.queued_write_to_device(cmd)


## Main loop
try:
    while True:
        ## Chat updates
        # Update chatter
        chatter.update(echo_to_stdout=True)

        start_message = "Parameters set. Press CTRL+C to start."

except KeyboardInterrupt:
    print "Keyboard interrupt received"
    chatter.queued_write_to_device(TrialSpeak.command_release_trial()) 

except:
    raise


print "The rest of the code goes here."