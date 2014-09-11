# Test script for SimpleTrialRelease
import ArduFSM
import TrialSpeak, TrialMatrix
import numpy as np

logfilename = 'out.log'
chatter = ArduFSM.chat.Chatter(to_user=logfilename, baud_rate=115200, 
    serial_timeout=.1)

# The ones that are fixed at the beginning
initial_params = {
    'MRT': 3,
    'RWSD': 1,
    'STPPOS': 1,
    'SRVPOS': 1,
    'ITI': 3000,
    }

def generate_trial_params(trial_matrix):
    """Given trial matrix so far, generate params for next"""
    res = {}
    # First check that the last trial hasn't been released
    assert trial_matrix['release_time'].isnull().irow(-1)
    
    # But that it has been responded
    assert not trial_matrix['response'].isnull().irow(-1)
    
    if len(trial_matrix) < 2:
        res['RWSD'] = 1
    else:
        # Get last trial
        last_trial = trial_matrix.irow(-1)
        if last_trial['response'] == last_trial['rwsd']:
            res['RWSD'] = {1: 2, 2:1}[last_trial['rwsd']]
        else:
            res['RWSD'] = last_trial['rwsd']
    
    res['STPPOS'] = np.random.randint(1, 10)
    res['SRVPOS'] = np.random.randint(1, 10)
    res['ITI'] = np.random.randint(10000)
    
    return res

## Main loop
last_released_trial = 0
try:
    while True:
        # Update chatter
        chatter.update(echo_to_stdout=True)
        
        # Check log
        splines = TrialSpeak.load_splines_from_file(logfilename)
        trial_matrix = TrialMatrix.make_trials_info_from_splines(splines)
        
        # Switch on which trial, and whether it's been released and/or completed
        if trial_matrix is None: # or if splines is empty?
            # It's the first tiral
            # Send each initial param
            for param_name, param_val in initial_params.items():
                chatter.write_to_device(
                    TrialSpeak.command_set_parameter(
                        param_name, param_val))            
            
            # Release
            chatter.write_to_device(TrialSpeak.command_release_trial())
        elif 'response' not in trial_matrix or trial_matrix['response'].isnull().irow(-1):
            # Trial has not completed, keep waiting
            continue
        elif last_released_trial == len(trial_matrix):
            # Trial has been completed, and already released
            continue
        else:
            # Trial has been completed, and needs to be released
            params = generate_trial_params(trial_matrix)

            # Set them
            for param_name, param_val in params.items():
                chatter.write_to_device(
                    TrialSpeak.command_set_parameter(
                        param_name, param_val))
            
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
