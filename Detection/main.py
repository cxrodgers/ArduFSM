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


## Find out what rig we're in using the current directory
this_dir_name = os.getcwd()
rigname = os.path.split(this_dir_name)[1]
serial_port = mainloop.get_serial_port(rigname)
#~ serial_port = '/dev/ttyACM0'

if not os.path.exists(serial_port):
    raise OSError("serial port %s does not exist" % serial_port)

## Get params
params_table = mainloop.get_params_table()
params_table = mainloop.assign_rig_specific_params(rigname, params_table)
params_table['current-value'] = params_table['init_val'].copy()

## Upload
if raw_input('Reupload protocol [y/N]? ').upper() == 'Y':
    if rigname in ['L0']:
        protocol_name = 'Detection'
    else:
        protocol_name = 'TwoChoice_%s' % rigname
    os.system('arduino --board arduino:avr:uno --port %s \
        --pref sketchbook.path=/home/chris/dev/ArduFSM \
        --upload ~/dev/ArduFSM/%s/%s.ino' % (
        serial_port, protocol_name, protocol_name))
    
    # Should look for programmer is not responding in output and warn user
    # to plug/unplug arduino

## Create Chatter
logfilename = 'out.log'
logfilename = None # autodate
chatter = ArduFSM.chat.Chatter(to_user=logfilename, to_user_dir='./logfiles',
    baud_rate=9600, serial_timeout=.1, serial_port=serial_port)
logfilename = chatter.ofi.name

## Initialize UI
RUN_GUI = False
ECHO_TO_STDOUT = True

## Main loop
final_message = None
try:
    ## Initialize GUI
    if RUN_GUI:
        plotter = ArduFSM.plot.PlotterWithServoThrow(trial_types)
        plotter.init_handles()
        if rigname == 'L1':
            plotter.graphics_handles['f'].canvas.manager.window.move(500, 0)
        elif rigname == 'L2':
            plotter.graphics_handles['f'].canvas.manager.window.move(500, 400)
        elif rigname == 'L3':
            plotter.graphics_handles['f'].canvas.manager.window.move(500, 800)
        elif rigname == 'L5':
            plotter.graphics_handles['f'].canvas.manager.window.move(500, 1000)
        elif rigname == 'L6':
            plotter.graphics_handles['f'].canvas.manager.window.move(500, 1400)
            
        elif rigname == 'L0':
            plotter.graphics_handles['f'].canvas.manager.window.wm_geometry("+700+0")
        
        plotter2 = ArduFSM.plot.LickPlotter()
        plotter2.init_handles()
        last_updated_trial = 0
    
    while True:
        ## Chat updates
        # Update chatter
        chatter.update(echo_to_stdout=ECHO_TO_STDOUT)
        
        # Read lines and split by trial
        # Could we skip this step if chatter reports no new device lines?
        #~ logfile_lines = TrialSpeak.read_lines_from_file(logfilename)
        #~ splines = TrialSpeak.split_by_trial(logfile_lines)

        ## Update GUI
        # Put this in it's own try/except to catch plotting bugs
        if RUN_GUI:
            if last_updated_trial < len(translated_trial_matrix):
                # update plot
                plotter.update(logfilename)     
                last_updated_trial = len(translated_trial_matrix)
                
                # don't understand why these need to be here
                #~ plt.show()
                #~ plt.draw()
            
            plotter2.update(logfile_lines)
            plt.show()
            plt.draw()

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
    
    if RUN_GUI:
        pass
        #~ plt.close(plotter.graphics_handles['f'])
        #~ print "GUI closed"
    
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


