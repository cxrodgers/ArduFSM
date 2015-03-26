# Test script for SimpleTrialRelease
import ArduFSM

logfilename = 'out.log'
chatter = ArduFSM.chat.Chatter(to_user=logfilename, baud_rate=115200, 
    serial_timeout=.1, serial_port='/dev/ttyACM0')


# The ones that are fixed at the beginning
initial_params = {
    }


## Main loop
last_released_trial = -1
try:
    while True:
        # Update chatter
        chatter.update(echo_to_stdout=True)
        
        # Check log
        splines = ArduFSM.TrialSpeak.load_splines_from_file(logfilename)
        trial_matrix = ArduFSM.TrialMatrix.make_trials_info_from_splines(splines)
        
        # Switch on which trial, and whether it's been released and/or completed
        if trial_matrix is None: # or if splines is empty?
            # It's the first tiral
            # Send each initial param   
            
            # Release
            chatter.write_to_device(ArduFSM.TrialSpeak.command_release_trial())
        elif 'resp' not in trial_matrix or (len(trial_matrix) > 0 and trial_matrix['resp'].isnull().irow(-1)):
            # Trial has not completed, keep waiting
            continue
        elif last_released_trial == len(trial_matrix):
            # Trial has been completed, and already released
            continue
        else:
            # Trial has been completed, and needs to be released
            
            # Release
            chatter.write_to_device(ArduFSM.TrialSpeak.command_release_trial())
            
            last_released_trial = len(trial_matrix)
        

## End cleanly upon keyboard interrupt signal
except KeyboardInterrupt:
    print "Keyboard interrupt received"
except:
    raise
finally:
    chatter.close()
    print "Closed."



