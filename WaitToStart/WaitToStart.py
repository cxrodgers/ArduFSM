
"""
    Main script to run to run WaitToStart behavior
    This is an example of how to write a protocol that sends parameters
    to the Arduino, then displays a message to the user, then starts
    the behavior once the user presses enter.
    This works by sending a start signal

    In each loop:
        * Updates chatter until two set variables are set on arduino side
        * Once variables set, wait for Keyboard Input to send start signal

"""

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




## Create Chatter
logfilename = None # autodate
chatter = ArduFSM.chat.Chatter(to_user=logfilename, to_user_dir='./logfiles',
    baud_rate=115200, serial_timeout=.1, 
    serial_port='/dev/tty.usbmodem1421')
logfilename = chatter.ofi.name

## Initialize UI

# Set the parameters
# In this example, LIGHTON designates duration in which house light stays on in ms, and
# LIGHTOFF designates duration in which house light stays off in ms
cmd = TrialSpeak.command_set_parameter('LIGHTON', 1000) 
chatter.queued_write_to_device(cmd)
cmd = TrialSpeak.command_set_parameter('LIGHTOFF', 4000) 
chatter.queued_write_to_device(cmd)

PARAMS_SET = False
start_message = "Parameters set. Press CTRL+C to start."
## Main loop
try:
    while True:
        ## Chat updates
        # Update chatter
        chatter.update(echo_to_stdout=True)

        if not PARAMS_SET and len(chatter.queued_writes) == 0:
            # time.sleep(4)
            PARAMS_SET = True
            print start_message

        

except KeyboardInterrupt:
    chatter.queued_write_to_device(TrialSpeak.command_release_trial()) 
    while True:
        chatter.update(echo_to_stdout=True)

except:
    raise

print "The rest of the code goes here."