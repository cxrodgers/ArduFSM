# Test script for SimpleTrialRelease
import ArduFSM
import ArduFSM.chat2
import TrialSpeak, TrialMatrix
import numpy as np, pandas
import my
import time
import curses
import trial_setter_ui

logfilename = 'out.log'
chatter = ArduFSM.chat2.Chatter(to_user=logfilename, baud_rate=115200, 
    serial_timeout=.1, serial_port='/dev/ttyACM0')

# The ones that are fixed at the beginning
initial_params = {
    'MRT': 3,
    'RWIN': 10000,
    }

# Define the possible types of trials here
# This should be loaded from disk, not written to disk.
trial_types = pandas.DataFrame.from_records([
    {'name':'CV-L-1150-050', 'srvpos':1150, 'stppos':50, 'rewside':'left',},
    {'name':'CC-R-1150-150', 'srvpos':1150, 'stppos':150, 'rewside':'right',},
    {'name':'CV-L-1175-050', 'srvpos':1175, 'stppos':50, 'rewside':'left',},
    {'name':'CC-R-1175-150', 'srvpos':1175, 'stppos':150, 'rewside':'right',},
    ])
trial_types.to_pickle('trial_types_2stppos')


def generate_trial_params(trial_matrix):
    """Given trial matrix so far, generate params for next"""
    res = {}
    
    if len(trial_matrix) == 0:
        # First trial, so pick at random from trial_types
        idx = trial_types.index[np.random.randint(0, len(trial_types))]
        res['RWSD'] = trial_types['rewside'][idx]
        res['STPPOS'] = trial_types['stppos'][idx]
        res['SRVPOS'] = trial_types['srvpos'][idx]
        res['ITI'] = np.random.randint(10000)
    
    else:    
        # Not the first trial
        # First check that the last trial hasn't been released
        assert trial_matrix['release_time'].isnull().irow(-1)
        
        # But that it has been responded
        assert not trial_matrix['choice'].isnull().irow(-1)
        
        # Set side to left by default, and otherwise forced alt
        if len(trial_matrix) < 2:
            res['RWSD'] = 'left'
        else:
            # Get last trial
            last_trial = trial_matrix.irow(-1)
            if last_trial['choice'] == last_trial['rewside']:
                res['RWSD'] = {'left': 'right', 'right':'left'}[last_trial['rewside']]
            else:
                res['RWSD'] = last_trial['rewside']
        
        # Use the forced side to choose from trial_types
        sub_trial_types = my.pick_rows(trial_types, rewside=res['RWSD'])
        assert len(sub_trial_types) > 0
        idx = sub_trial_types.index[np.random.randint(0, len(sub_trial_types))]
        
        res['STPPOS'] = trial_types['stppos'][idx]
        res['SRVPOS'] = trial_types['srvpos'][idx]
        res['ITI'] = np.random.randint(10000)
        
    # Untranslate the rewside
    # This should be done more consistently, eg, use real phrases above here
    # and only untranslate at this point.
    res['RWSD'] = {'left': 1, 'right': 2}[res['RWSD']]
    
    return res


def choose_params_send_and_release(translated_trial_matrix):
    """Choose params for next unreleased trial, send, and release."""
    params = generate_trial_params(translated_trial_matrix)

    # Set them
    for param_name, param_val in params.items():
        chatter.queued_write_to_device(
            TrialSpeak.command_set_parameter(
                param_name, param_val))
    
    # Release
    chatter.queued_write_to_device(TrialSpeak.command_release_trial())    

def is_current_trial_incomplete(translated_trial_matrix):
    if len(translated_trial_matrix) < 1:
        raise ValueError("no trials have begun")
    if 'choice' not in translated_trial_matrix.columns:
        raise ValueError("need translated matrix")
    
    return translated_trial_matrix['choice'].isnull().irow(-1)


## Initialize UI
ui_params = initial_params.items()
ui_scheduler = {
    'name': 'forced alternation',
    'params': [
        ('FD', 'R'),
        ('RPB', 1000),
        ]
    }

RUN_UI = True
if RUN_UI:
    ui = trial_setter_ui.UI(timeout=1000, chatter=chatter, logfilename=logfilename,
        params=ui_params, scheduler=ui_scheduler)

    try:
        ui.start()
    except:
        ui.close()
        print "error encountered when starting UI"
        raise
    


## Main loop
initial_params_sent = False
last_released_trial = -1
final_message = None
try:
    while True:
        ## Chat updates
        # Update chatter
        chatter.update(echo_to_stdout=False)
        
        # Read lines and split by trial
        logfile_lines = TrialSpeak.read_lines_from_file(logfilename)
        splines = TrialSpeak.split_by_trial(logfile_lines)

        ## Initialization stuff
        # Behavior depends on how much data has been received
        if len(splines) == 0:
            # No data received, or possibly munged data received.
            # Add some more error checks for this   
            # Are we starting at time 0? Is the encoding corrupted?
            # Is the TrialSpeak version right?
            continue
        if len(splines) == 1:
            # Some data has been received, so the Arduino has booted up.
            # Add an error check that it is speaking our language here.
            # But no trials have occurred yet (splines[0] is setup info).
            # Send initial params if they haven't already been sent
            if not initial_params_sent:
                # Send each initial param
                for param_name, param_val in initial_params.items():
                    cmd = TrialSpeak.command_set_parameter(param_name, param_val)           
                    chatter.queued_write_to_device(cmd)
                
                # Mark as sent
                initial_params_sent = True

        ## Construct trial_matrix
        # Now we know that the Arduino has booted up and that the initial
        # params have been sent.
        # Construct trial_matrix
        trial_matrix = TrialMatrix.make_trials_info_from_splines(splines)
        current_trial = len(trial_matrix) - 1
        
        # Translate
        translated_trial_matrix = TrialSpeak.translate_trial_matrix(trial_matrix)
        
        ## Trial releasing logic
        # Was the last released trial the current one or the next one?
        if last_released_trial < current_trial:
            raise "unreleased trials have occurred, somehow"
            
        elif last_released_trial == current_trial:
            # The current trial has been released, or no trials have been released
            if current_trial == -1:
                # first trial has not even been released yet, nor begun
                choose_params_send_and_release(translated_trial_matrix)            
                last_released_trial = current_trial + 1
            elif is_current_trial_incomplete(translated_trial_matrix):
                # Current trial has been released but not completed
                pass
            else:
                # Current trial has been completed. Next trial needs to be released.
                choose_params_send_and_release(translated_trial_matrix)                
                last_released_trial = current_trial + 1            
        
        elif last_released_trial == current_trial + 1:
            # Next trial has been released, but has not yet begun
            pass
        
        else:
            raise "too many trials have been released, somehow"
        
        
        ## Update UI
        if RUN_UI:
            ui.update_data(logfile_lines=logfile_lines)
            ui.get_and_handle_keypress()
            


## End cleanly upon keyboard interrupt signal
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
    


