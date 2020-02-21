# A simple standalone script to communicate with the Arduino
# This one tests the chat library, without anything else
# It sends SET messages to test functionality
#
# To upload sketch:
# arduino --board arduino:avr:uno --port /dev/ttyACM0 --pref sketchbook.path=/home/jung/dev/ArduFSM --upload testchat2.ino
# And then just run this script.

from time import sleep
import serial

# If True, sends messages and listens
# If False, just listens
SEND_MESSAGES = True

with serial.Serial('/dev/ttyACM0', 115200, timeout=.1) as ser:
    for n_message in range(100):
        # Optionally send a message
        if SEND_MESSAGES:
            if n_message % 10 == 5:
                # Generate the message 
                # It must end in \r\n
                message = 'SET RD_L 69\r\n'
                message_bytes = bytes(message, 'utf-8')
                
                # Write the message
                print("Sending: %r" % message_bytes)
                ser.write(message_bytes)

        # Wait for a response, if any
        # This seems to return b'', not None, if timeout occurs
        response_bytes = ser.readline()
        response_string = response_bytes.decode('utf-8')

        # Print the response
        print("Response: %r" % response_string)

