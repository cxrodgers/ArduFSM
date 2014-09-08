# Test script for SimpleTrialRelease
import ArduFSM


chatter = ArduFSM.chat.Chatter(to_user='out.log', baud_rate=115200, serial_timeout=.1)#~ chatter.loop_till_interrupt()

## Main loop
try:
    while True:
        chatter.update(echo_to_stdout=True)

## End cleanly upon keyboard interrupt signal
except KeyboardInterrupt:
    print "Keyboard interrupt received"
except:
    raise
finally:
    chatter.close()
    print "Closed."
