# Test script for SimpleTrialRelease
import ArduFSM
import TrialSpeak, TrialMatrix
import numpy as np, pandas
import my
import time

logfilename = 'out.log'
chatter = ArduFSM.chat.Chatter(to_user=logfilename, baud_rate=115200, 
    serial_timeout=.1, serial_port='/dev/ttyACM0')

# The ones that are fixed at the beginning
initial_params = {
    'MRT': 3,
    'RWSD': 1,
    'STPPOS': 1,
    'SRVPOS': 1,
    'ITI': 3000,
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

## Main loop
last_released_trial = -1
try:
    while True:
        # Update chatter
        chatter.update(echo_to_stdout=True)
        
        # Check log
        splines = TrialSpeak.load_splines_from_file(logfilename)
        
        # Really we should wait until we hear something from the arduino
        # Simply wait till at least one line has been received
        if len(splines) == 0 or len(splines[0]) == 0:
            continue

        # Construct trial_matrix. I believe this will always have at least
        # one line in it now, even if it's composed entirely of Nones.
        trial_matrix = TrialMatrix.make_trials_info_from_splines(splines)
        translated_trial_matrix = TrialSpeak.translate_trial_matrix(trial_matrix)
        
        # Switch on which trial, and whether it's been released and/or completed
        #if len(splines) == 0: # or trial_matrix is None?: # or if splines is empty?
        if last_released_trial == -1:
            # It's the first tiral
            # Send each initial param
            for param_name, param_val in initial_params.items():
                cmd = TrialSpeak.command_set_parameter(param_name, param_val)           
                chatter.write_to_device(cmd)
            
            # Release
            chatter.write_to_device(TrialSpeak.command_release_trial())
            last_released_trial = 0
            
        elif 'resp' not in trial_matrix or trial_matrix['resp'].isnull().irow(-1):
            # Trial has not completed, keep waiting
            continue
        elif last_released_trial == len(trial_matrix):
            # Trial has been completed, and already released
            continue
        else:
            # Trial has been completed, and needs to be released
            params = generate_trial_params(translated_trial_matrix)

            # Set them
            for param_name, param_val in params.items():
                chatter.write_to_device(
                    TrialSpeak.command_set_parameter(
                        param_name, param_val))
                time.sleep(1.0)
            
            # Release
            chatter.write_to_device(TrialSpeak.command_release_trial())
            
            last_released_trial = len(trial_matrix)
        

## End cleanly upon keyboard interrupt signal
except KeyboardInterrupt:
    print "Keyboard interrupt received"
except:
    raise
finally:
    chatter.close()
    print "Closed."
