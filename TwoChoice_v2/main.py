# Main script to run to run TwoChoice_v2 behavior
# Timings: set 'serial_timeout' in chatter, and 'timeout' in UI, to be low
# enough that the response is quick, but not so low that it takes up all the
# CPU power.
# Right now, it does this on each loop
# * Update chatter (timeout)
# * Update UI (timeout)
# * do other things, like reading logfile and setting next trial
# So, if the timeouts are too low, it spends a lot more time reading the
# logfile and there is more overhead overall.

import sys
import os
import numpy as np, pandas
import my
import time
import curses
import matplotlib.pyplot as plt

# Ardu imports
tcv2_path = os.path.expanduser('~/dev/ArduFSM/TwoChoice_v2')
if tcv2_path not in sys.path:
    sys.path.append(tcv2_path)
import ArduFSM
import ArduFSM.chat2
import ArduFSM.plot2
import TrialSpeak, TrialMatrix
import trial_setter_ui
import Scheduler
import trial_setter2
import mainloop


## Find out what rig we're in using the current directory
this_dir_name = os.getcwd()
rigname = os.path.split(this_dir_name)[1]
serial_port = mainloop.get_serial_port(rigname)

## Get params
params_table = mainloop.get_params_table()
params_table = mainloop.assign_rig_specific_params(rigname, params_table)
params_table['current-value'] = params_table['init_val'].copy()

## Get trial types
trial_types = mainloop.get_trial_types('trial_types_3srvpos')

## Initialize the scheduler
scheduler = Scheduler.SessionStarter(trial_types=trial_types)

## Create Chatter
logfilename = 'out.log'
logfilename = None # autodate
chatter = ArduFSM.chat2.Chatter(to_user=logfilename, to_user_dir='./logfiles',
    baud_rate=115200, serial_timeout=.1, serial_port=serial_port)
logfilename = chatter.ofi.name

## Trial setter
ts_obj = trial_setter2.TrialSetter(chatter=chatter, 
    params_table=params_table,
    scheduler=scheduler)

## Initialize UI
RUN_UI = True
RUN_GUI = True
ECHO_TO_STDOUT = not RUN_UI
if RUN_UI:
    ui = trial_setter_ui.UI(timeout=100, chatter=chatter, 
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
        plotter = ArduFSM.plot2.PlotterWithServoThrow(trial_types)
        plotter.init_handles()
        last_updated_trial = 0
    
    while True:
        ## Chat updates
        # Update chatter
        chatter.update(echo_to_stdout=ECHO_TO_STDOUT)
        
        # Read lines and split by trial
        # Could we skip this step if chatter reports no new device lines?
        logfile_lines = TrialSpeak.read_lines_from_file(logfilename)
        splines = TrialSpeak.split_by_trial(logfile_lines)

        # Run the trial setting logic
        translated_trial_matrix = ts_obj.update(splines)
        
        ## Meta-scheduler
        # Not sure how to handle this yet. Probably should be an object
        # ts_obj.meta_scheduler that can change ts_obj.scheduler, or a method
        # meta_scheduler(trial_matrix) that returns the new scheduler
        # Actually, probably makes the most sense to have each meta-scheduler
        # just be a scheduler called "auto" or something.
        if len(translated_trial_matrix) > 8 and ts_obj.scheduler.name == 'session starter':
            new_scheduler = Scheduler.ForcedAlternation(trial_types=trial_types)
            ts_obj.scheduler = new_scheduler
        
        ## Update UI
        if RUN_UI:
            ui.update_data(logfile_lines=logfile_lines)
            ui.get_and_handle_keypress()

        ## Update GUI
        # Put this in it's own try/except to catch plotting bugs
        if RUN_GUI:
            if last_updated_trial < len(translated_trial_matrix):
                # update plot
                plotter.update(logfilename)     
                last_updated_trial = len(translated_trial_matrix)
                
                # don't understand why these need to be here
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
    
    if RUN_UI:
        ui.close()
        print "UI closed"
    
    if RUN_GUI:
        plt.close(plotter.graphics_handles['f'])
        print "GUI closed"
    
    if final_message is not None:
        print final_message
    


