from __future__ import print_function
# Test script for SimpleTrialRelease
import ArduFSM

chatter = ArduFSM.chat.Chatter(to_user='out.log', baud_rate=115200, 
    serial_timeout=.1, serial_port='/dev/ttyACM1')


## Main loop
try:
    while True:
        chatter.update(echo_to_stdout=True)

## End cleanly upon keyboard interrupt signal
except KeyboardInterrupt:
    print("Keyboard interrupt received")
except:
    raise
finally:
    chatter.close()
    print("Closed.")
