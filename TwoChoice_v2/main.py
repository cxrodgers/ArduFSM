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


"""
TODO
* Mark forced trials.
* Fix the timing before RWIN
* Allow setting of touch/release thresholds
* Allow setting param by cursor
* Keep track of manual rewards in reward count
"""

import ArduFSM
import ArduFSM.chat2
import ArduFSM.plot2
import TrialSpeak, TrialMatrix
import numpy as np, pandas
import my
import time
import curses
import trial_setter_ui
import Scheduler
import trial_setter2
import matplotlib.pyplot as plt

## Create Chatter
logfilename = 'out.log'
chatter = ArduFSM.chat2.Chatter(to_user=logfilename, baud_rate=115200, 
    serial_timeout=.1, serial_port='/dev/ttyACM1')

## Params
YES = 3
NO = 2
MD = 0

"""Params table

These are all the parameters that the Arduino code uses.
Columns:
    name            The abbreviation used to set the param.
    init_val        The value that the Python code uses by default, if it isn't
                    set in any other way. If this is MD ("must-define"),
                    then it must be set by something, either at the beginning
                    of the session or on each trial.
    required_ET     If True, then it is required to be set on each trial.
                    Currently this is ignored, though we should implement
                    error checking for it on both sides.
    reported_ET     If True, then its value is reported by the Arduino on 
                    each trial, using the TRLP command.
                    Currently this is hand-copied to the Arduino code.
                    Eventually, we probably want to default to all params
                    reported and no params required, and then set it from
                    Python side.
    ui_accessible   If True, then the UI provides a mechanism for setting it.
                    This is simply to make the UI less overwhelming, and
                    because some params seem unlikely to ever change during
                    a session.
    rig_dependent   If True, then this parameter is expected to vary by rig.
                    A rig-specific params file will be loaded and used to
                    set this param. If it is not specified by that file,
                    its init_val is used (unless it is MD).
    send_on_init    If True, then this parameter is sent before the first
                    trial begins. Any param that is not send_on_init and
                    not required_ET will use Arduino defaults, which really
                    only applies to params that we don't expect to ever change.

Note that the value 0 may never be sent to the Arduino, due to limitations
in the Arudino-side conversion of strings to int. To send boolean values,
use YES and NO. It is undetermined whether negative values should be allowed.

We currently define MD as 0, since this is not an allowable value to send.
"""
params_table = pandas.DataFrame([
    ('STPPOS',  MD,       1, 1, 0, 0, 0),
    ('RWSD',    MD,       1, 1, 0, 0, 0),
    ('SRVPOS',  MD,       1, 1, 0, 0, 0),
    ('RD_L',    MD,       0, 0, 1, 1, 1),
    ('RD_R',    MD,       0, 0, 1, 1, 1),
    ('ITI',     1000,     0, 0, 1, 0, 1),
    ('PSW',     1,        0, 0, 1, 0, 0),
    ('TOE',     YES,      0, 0, 1, 0, 1),
    ('MRT',     1,        0, 0, 1, 0, 1),
    ('STPSPD',  MD,       0, 0, 0, 1, 0),
    ('STPFR',   50,       0, 0, 0, 1, 0),
    ('2PSTP',   MD,       0, 0, 0, 1, 1),
    ('SRVST',   1000,     0, 0, 0, 1, 0),
    ('STPIP',   50,       0, 0, 0, 1, 1),
    ('SRVFAR',  1900,     0, 0, 0, 1, 1),
    ('SRVTT',   MD,       0, 0, 0, 1, 1),
    ('RWIN',    45000,    0, 0, 0, 0, 1),
    ('IRI',     500,      0, 0, 0, 0, 0),    
    ],
    columns=('name', 'init_val', 'required_ET', 'reported_ET', 
        'ui-accessible', 'rig-dependent', 'send_on_init'),
    ).set_index('name')
bool_list = ['required_ET', 'reported_ET', 'ui-accessible', 
    'rig-dependent', 'send_on_init']
params_table[bool_list] = params_table[bool_list].astype(np.bool)

# Assign the rig-specific by hand for now
params_table['init_val']['STPSPD'] = 20
params_table['init_val']['2PSTP'] = NO
params_table['init_val']['SRVTT'] = 4000
params_table['init_val']['RD_L'] = 20
params_table['init_val']['RD_R'] = 25

# Column for current value
params_table['current-value'] = params_table['init_val'].copy()

## Initialize the scheduler
trial_types = pandas.read_pickle('trial_types_2stppos')
scheduler = Scheduler.RandomStim(trial_types=trial_types)

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

    except:
        ui.close()
        print "error encountered when starting UI"
        raise

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
    


