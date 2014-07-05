import serial
import time
import datetime
import os
import sys
import errno

## From device to user
def read_from_device(device):
    """Receives information from device and appends"""
    new_lines = device.readlines()
    return new_lines

def write_to_user(buffer, data):
    """Write `data` to the user via `buffer`
    
    `buffer` : a file
    """
    # No matter what, pipe new_lines to savefile here
    for line in data:
        buffer.write(line)
    buffer.flush()


## From user to device
def read_from_user(buffer, buffer_size=1024):
    """Read what the user wrote and returns it
    
    `buffer`: a named pipe
    """
    try:
        data = os.read(buffer, buffer_size)
    except OSError as err:
        # Test whether this is the expected error
        if (err.errno == errno.EAGAIN or 
            err.errno == errno.EWOULDBLOCK):
            # Expected error when nothing arrives
            data = None
        else:
            # Unexpected error
            raise
    
    return data

def write_to_device(device, data):
    if data is not None:
        device.write(data)


class Chatter:
    """Object to manage chat between serial device and user.
    
    The user may write text to an input pipe, and it will be relayed to
    the device on every `update` call.
    
    Additionally, anything received from the device will be written to an
    output file and optionally echoed to stdout on every `update` call.
    
    Call `close` to shut down the connections.
    
    Call `main_loop` to iterate over `update` calls until CTRL+C is received.
    """
    def __init__(self, serial_port='/dev/ttyACM0', from_user='TO_DEV', 
        to_user=None, serial_timeout=0.01, baud_rate=9600):
        """Initialize a new Chatter.
        
        `serial_port` : where the device is located
        `from_user` : name of pipe to use to collect user's input
        `to_user` : name of file to print information from the device
        """
        ## Set up TO_DEV
        # Read from this pipe whenever something writes to it, and send
        # to device
        if not os.path.exists(from_user):
            os.mkfifo(from_user)
        self.pipein = os.open(from_user, os.O_RDONLY | os.O_NONBLOCK)

        ## Set up FROM_DEV
        # where to put stuff from the device
        if to_user is None:
            to_user = 'ardulines.' + \
                datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        self.ofi = file(to_user, 'w')

        ## Set up device
        # 0 means return whatever is available immediately
        # otherwise, wait for specified time
        # 0.01 takes a noticeable but small amount of CPU time
        self.ser = serial.Serial(serial_port, baud_rate, timeout=serial_timeout)

        # Wait for it to initialize the arduino
        time.sleep(1) # without this sleep, still leftover input from previous run
        self.ser.flushInput() # otherwise still input from previous run pending
        time.sleep(1) # without this sleep, it will not send the first line or so to the device
        
        # these don't appear to be necessary??
        #~ self.ser.flush()
        #~ self.ser.flushOutput()
        
        self.new_user_text = ''
        self.new_device_lines = []

    def update(self, echo_to_stdout=True):
        # Read any new text from the user and send to device
        self.new_user_text = read_from_user(self.pipein)
        write_to_device(self.ser, self.new_user_text)
        
        # Read any new lines from the device and send to user
        self.new_device_lines = read_from_device(self.ser)
        write_to_user(self.ofi, self.new_device_lines)
        
        # Echo
        if echo_to_stdout:
            write_to_user(sys.stdout, self.new_device_lines)
            sys.stdout.flush()
        
        # Pause for a bit
        #~ time.sleep(.010)   

    def close(self):
        self.ser.close()
        self.ofi.close()
        #pipein.close()
    
    def write_to_device(self, string, auto_newline=True):
        """Write a line to the device.
        
        Adds a newline character automatically if necessary.
        Does not call update.
        """
        if auto_newline and not string.endswith('\n'):
            string = string + '\n'
        write_to_device(self.ser, string)


def loop_till_interrupt(chatter):
    ## Main loop
    try:
        while True:
            chatter.update()

    ## Clean endings
    except KeyboardInterrupt:
        print "Keyboard interrupt received"
    except:
        raise
    finally:
        chatter.close()
        print "Closed."
