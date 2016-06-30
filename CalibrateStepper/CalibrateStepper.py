# Main script to run to run CalibrateStepper behavior
# Only sets parameters concerning stepper motor and servo motor movements
# Receives voltage values from hall sensor and plots in a graph

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

def move_figure(f, x, y):
    """Move figure's upper left corner to pixel (x, y)"""
    backend = matplotlib.get_backend()
    if backend == 'TkAgg':
        f.canvas.manager.window.wm_geometry("+%d+%d" % (x, y))
    elif backend == 'WXAgg':
        f.canvas.manager.window.SetPosition((x, y))
    else:
        # This works for QT and GTK
        # You can also use window.setGeometry
        f.canvas.manager.window.move(x, y)
    plt.show()


# Load the parameters file
with file('parameters.json') as fi:
    runner_params = json.load(fi)

# Check the serial port exists
if not os.path.exists(runner_params['serial_port']):
    raise OSError("serial port %s does not exist" % 
        runner_params['serial_port'])



# sensor plot
SHOW_SENSOR_PLOT = True




## Create Chatter
logfilename = None # autodate
chatter = ArduFSM.chat.Chatter(to_user=logfilename, to_user_dir='./logfiles',
    baud_rate=115200, serial_timeout=.1, 
    serial_port=runner_params['serial_port'])
logfilename = chatter.ofi.name

params = {
            'SRVFAR' : 1100,
            'SRVST'  : 1000,
            'STPSPD' : 30,
            'STPIP'  : 50,
         }

trial_setter.send_params_and_release(params, chatter)



## Initialize UI
RUN_UI = False
RUN_GUI = True
ECHO_TO_STDOUT = not RUN_UI
ui_obj = trial_setter_ui.UI
if RUN_UI:
    ui = ui_obj(timeout=200, chatter=chatter, 
        logfilename=logfilename,
        ts_obj=ts_obj)

    try:
        ui.start()

    except curses.error as err:
        raise Exception(
            "UI error. Most likely the window is, or was, too small.\n"
            "Quit Python, type resizewin to set window to 80x23, and restart.")

    except:
        print "error encountered when starting UI"
        raise
    
    finally:
        ui.close()


## Main loop
final_message = None
try:
    
    ## Initialize GUI
    if RUN_GUI:
        # plotter = ArduFSM.plot.PlotterWithServoThrow(trial_types)
        # plotter.init_handles()
        # move_figure(plotter.graphics_handles['f'],
        #     gui_window_position[0], gui_window_position[1])
        
        # if SHOW_IR_PLOT:
        #     plotter2 = ArduFSM.plot.LickPlotter()
        #     plotter2.init_handles()
        #     if window_position_IR_plot is not None:
        #         move_figure(plotter2.handles['f'],
        #             window_position_IR_plot[0], window_position_IR_plot[1])
        
        if SHOW_SENSOR_PLOT:
            sensor_plotter = ArduFSM.plot.SensorPlotter()
            sensor_plotter.init_handles()
        
        last_updated_trial = 0
        
    while True:
        ## Chat updates
        # Update chatter
        chatter.update(echo_to_stdout=ECHO_TO_STDOUT)
        
        # Read lines and split by trial
        # Could we skip this step if chatter reports no new device lines?
        logfile_lines = TrialSpeak.read_lines_from_file(logfilename)
        splines = TrialSpeak.split_by_trial(logfile_lines)

        #~ except ValueError:
            #~ raise ValueError("cannot get any lines; try reuploading protocol")
        
        ## Update UI
        if RUN_UI:
            ui.update_data(logfile_lines=logfile_lines)
            ui.get_and_handle_keypress()

        ## Update GUI
        # Put this in it's own try/except to catch plotting bugs
        if RUN_GUI:
            if SHOW_SENSOR_PLOT:
                sensor_plotter.update(logfile_lines)


            
                

except KeyboardInterrupt:
    print "Keyboard interrupt received"


except:
    raise

finally:
    chatter.close()
    print "chatter closed"

    
    if RUN_GUI:
        plt.show()
        #~ plt.close(plotter.graphics_handles['f'])
        #~ print "GUI closed"
    
    if final_message is not None:
        print final_message
    


