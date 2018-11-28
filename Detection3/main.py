# Main script to run to run Detection behavior

import sys
import os
import numpy as np, pandas
import my
import time
import curses
import matplotlib.pyplot as plt
import shutil

# Ardu imports. Because this is an example script that will be run in another
# directory, don't assume we can import TrialSpeak et al directly
import ArduFSM
from ArduFSM import TrialSpeak, TrialMatrix
from ArduFSM import trial_setter_ui
from ArduFSM import Scheduler
from ArduFSM import trial_setter
from ArduFSM import mainloop


## Serial port and protocol name
serial_port = '/dev/ttyACM0'
protocol_name = 'Detection3'

if not os.path.exists(serial_port):
    raise OSError("serial port %s does not exist" % serial_port)


## Upload
if raw_input('Reupload protocol [y/N]? ').upper() == 'Y':
    os.system('arduino --board arduino:avr:uno --port %s \
        --pref sketchbook.path=/home/chris/dev/ArduFSM \
        --upload ~/dev/ArduFSM/%s/%s.ino' % (
        serial_port, protocol_name, protocol_name)
    )
    
    # Should look for programmer is not responding in output and warn user
    # to plug/unplug arduino


## Create Chatter
logfilename = 'out.log'
logfilename = None # autodate
chatter = ArduFSM.chat.Chatter(to_user=logfilename, to_user_dir='./logfiles',
    baud_rate=9600, serial_timeout=.1, serial_port=serial_port)
logfilename = chatter.ofi.name


## Initialize UI
ECHO_TO_STDOUT = True

## Main loop
final_message = None
try:
    while True:
        ## Chat updates
        # Update chatter
        chatter.update(echo_to_stdout=ECHO_TO_STDOUT)

except KeyboardInterrupt:
    print "Keyboard interrupt received"

except trial_setter_ui.QuitException as qe:
    final_message = qe.message

except curses.error as err:
    raise Exception(
        "UI error. Most likely the window is, or was, too small.\n"
        "Quit Python, type resizewin to set window to 80x23, and restart.")

except:
    raise

finally:
    chatter.close()
    print "chatter closed"
    
    if final_message is not None:
        print final_message


## Save
filename = chatter.ofi.name
    
# Get mouse name
print "Filename:", filename
mousename = raw_input("Enter mouse name: ")
mousename = mousename.strip()

# Copy the file
if mousename != '':
    new_filename = filename + '.' + mousename
    assert not os.path.exists(new_filename)
    shutil.copyfile(filename, new_filename)  
    print "Saved file as", new_filename
else:
    print "no mouse name entered"


