# A simple standalone script to communicate with the Arduino
# Repeatedly sends messages, waits for a response (which should be a
# simple acknowledgement), prints the response.
#
# To upload sketch:
# arduino --board arduino:avr:uno --port /dev/ttyACM0 --upload testchat1.ino
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
                message = 'Message {}\r\n'.format(n_message)
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

