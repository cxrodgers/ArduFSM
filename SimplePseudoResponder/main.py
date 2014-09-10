# Test script for SimpleTrialRelease
import ArduFSM
import TrialSpeak, TrialMatrix

logfilename = 'out.log'
chatter = ArduFSM.chat.Chatter(to_user=logfilename, baud_rate=115200, 
    serial_timeout=.1)

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
                # Set the new ITI to the number of trials elapsed and release
                chatter.write_to_device(
                    TrialSpeak.command_set_parameter('ITI', len(splines) * 1000))
                chatter.write_to_device(TrialSpeak.command_release_trial())
        

## End cleanly upon keyboard interrupt signal
except KeyboardInterrupt:
    print "Keyboard interrupt received"
except:
    raise
finally:
    chatter.close()
    print "Closed."
