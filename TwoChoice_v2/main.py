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
import ArduFSM
import ArduFSM.chat2
import TrialSpeak, TrialMatrix
import numpy as np, pandas
import my
import time
import curses
import trial_setter_ui
import Scheduler
import trial_setter2

## Create Chatter
logfilename = 'out.log'
chatter = ArduFSM.chat2.Chatter(to_user=logfilename, baud_rate=115200, 
    serial_timeout=.1, serial_port='/dev/ttyACM0')

## Params
# These should be loaded from the protocol file, and also rig-specific file
# The ones that are fixed at the beginning
initial_params = {
    'MRT': 3,
    'RWIN': 10000,
    }

## Initialize the scheduler
trial_types = pandas.read_pickle('trial_types_2stppos')
scheduler = Scheduler.RandomStim(trial_types=trial_types)

## Trial setter
ts_obj = trial_setter2.TrialSetter(chatter=chatter, initial_params=initial_params,
    scheduler=scheduler)

## Initialize UI
ui_params = initial_params.items()
RUN_UI = True
ECHO_TO_STDOUT = not RUN_UI
if RUN_UI:
    ui = trial_setter_ui.UI(timeout=100, chatter=chatter, 
        logfilename=logfilename,
        params=ui_params, scheduler=scheduler)

    try:
        ui.start()
    except:
        ui.close()
        print "error encountered when starting UI"
        raise


## Main loop
final_message = None
try:
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
        
        ## Update UI
        if RUN_UI:
            ui.update_data(logfile_lines=logfile_lines)
            res = ui.get_and_handle_keypress()
            
            # Handle any change to scheduler (or params?)
            # Probably, ui should have a hook to trial_setter, so that it
            # can change ts_obj.scheduler directly.
            if res == 'schedule changed':
                ts_obj.scheduler = ui.scheduler

except KeyboardInterrupt:
    print "Keyboard interrupt received"

except trial_setter_ui.QuitException as qe:
    final_message = qe.message

except:
    raise

finally:
    chatter.close()
    if RUN_UI:
        ui.close()
    print "chatter and UI closed"
    
    if final_message is not None:
        print final_message
    


