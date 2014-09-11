# Test script for SimpleTrialRelease
import ArduFSM
import TrialSpeak, TrialMatrix
import numpy as np

logfilename = 'out.log'
chatter = ArduFSM.chat.Chatter(to_user=logfilename, baud_rate=115200, 
    serial_timeout=.1)


def generate_trial_params(trial_matrix):
    """Given trial matrix so far, generate params for next"""
    return {
        'ITI' : len(trial_matrix) * 1000,
        
        # A bunch of random params, all ignored
        'rewsiderewsiderewsiderewsiderewsiderewside' : np.random.randint(2),
        'stimulus' : np.random.randint(10),
        'speed' : np.random.randint(10),
        'texture' : np.random.randint(10),
        }

## Main loop
try:
    while True:
        # Update chatter
        chatter.update(echo_to_stdout=True)
        
        # Check log
        splines = TrialSpeak.load_splines_from_file(logfilename)
        trial_matrix = TrialMatrix.make_trials_info_from_splines(splines)
        
        # Release the last trial if it hasn't already happened
        # Actually what would probaby be better is to maintain an updated
        # trials_info, and then to check whether we've sent the release command,
        # rather than looking for ACK.
        if len(splines) >= 1:
            last_trial = splines[-1]
            
            # Release the trial if it hasn't happened already
            if not TrialSpeak.check_if_trial_released(last_trial):
                # Choose params
                params = generate_trial_params(trial_matrix)
                
                # Set them
                for param_name, param_val in params.items():
                    chatter.write_to_device(
                        TrialSpeak.command_set_parameter(
                            param_name, param_val))
                
                # Release
                chatter.write_to_device(TrialSpeak.command_release_trial())
        

## End cleanly upon keyboard interrupt signal
except KeyboardInterrupt:
    print "Keyboard interrupt received"
except:
    raise
finally:
    chatter.close()
    print "Closed."
