"""Main script to run to run WaitToStart behavior

This is an example of how to write a protocol that sends parameters
to the Arduino, then tells the Arduino to wait until the user presses
enter before it finishes setup() and starts loop().

This works by sending a start signal (which is the string "TRL_RELEASED")
over the serial port.

As an example, user-defined variables LIGHTON_DUR and LIGHTOFF_DUR set 
House Light duration.
"""

import ArduFSM
import os

# Create a directory to store logfiles in
logfile_dir = './logfiles'
if not os.path.exists(logfile_dir):
    os.mkdir(logfile_dir)

# Set this to be the correct serial port
serial_port = '/dev/tty.usbmodem1411'

# Create Chatter
logfilename = None # autodate
chatter = ArduFSM.chat.Chatter(to_user=logfilename, to_user_dir=logfile_dir,
    baud_rate=115200, serial_timeout=.1, 
    serial_port=serial_port)
logfilename = chatter.ofi.name

# Set the parameters
# In this example, LIGHTON_DUR designates duration in which house light 
# stays on in ms, and LIGHTOFF_DUR designates duration in which house light 
# stays off in ms
# These commands will be stored in the chatter's queue until they are sent
cmd = ArduFSM.TrialSpeak.command_set_parameter('LIGHTON_DUR', 5000) 
chatter.queued_write_to_device(cmd)
cmd = ArduFSM.TrialSpeak.command_set_parameter('LIGHTOFF_DUR',5000) 
chatter.queued_write_to_device(cmd)

# Main loop
try:
    # Wait for all the parameter-setting commands to be sent
    # We can tell they have been received because there will be no
    # writes remaining in the queue, and the arduino has acknowledged
    # the last sent line.
    while(len(chatter.queued_writes) > 0 or 
        not chatter.last_sent_line_acknowledged):
        # Update the chatter
        chatter.update(echo_to_stdout=True)

    # Wait for keyboard press then start updating again
    raw_input("Parameters set. Press enter to start.")

    # Sent the TRL_RELEASED signal
    # This tells the arduino to finish setup() and start loop()
    chatter.queued_write_to_device(ArduFSM.TrialSpeak.command_release_trial()) 
    
    # Wait until it is received and acknowledged
    # For some reason, program gets stuck at update if there is a line to be read
    while(len(chatter.queued_writes) > 0 or 
        not chatter.last_sent_line_acknowledged):
        # Update the chatter
        chatter.update(echo_to_stdout=True)
    print "Session has begun. Press CTRL+C to quit."
    
    # Now just update until CTRL+C is pressed
    while(True):
        chatter.update(echo_to_stdout=True)

except KeyboardInterrupt:
    print "Keyboard interrupt received"

finally:
    # Always close the chatter even if an error occurred
    chatter.close()
