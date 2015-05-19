# Adapted for Windows compatibility 
import serial
import time
import datetime
import os
import sys
import errno
# for Windows compatibility
import platform

if platform.system() == 'Windows':
    import win32pipe, win32file, win32event
    from_user = r'\\.\pipe\ardupipe'
    serial_port = 'COM4'
else:
    from_user = 'TO_DEV'
    serial_port = '/dev/ttyACM0'

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
    # I suspect this fails silently if the arduino's buffer is full
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

    def _create_pipe(self):
        """

        :rtype : object
        """
        if platform.system() == 'Windows':
            pipe = win32pipe.CreateNamedPipe(
                self.pipe_path,
                win32pipe.PIPE_ACCESS_DUPLEX | win32file.FILE_FLAG_OVERLAPPED, # open mode
                win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,  # blocking mode
                1,  # number of instances
                1024,  # output buffer size
                1024,  # input buffer size
                300,  # client time-out
                None)  # no security attributes

            ol = win32file.OVERLAPPED()
            ol.hEvent = win32event.CreateEvent(None, 0, 0, None)
        else:
            #try:
            os.mkfifo(self.pipe_path)
            #except FileExistsError:
            #    pass

            pipe, ol = None, None

        return pipe, ol

    def _connect_pipe(self, pipe, ol):
        """

        :rtype : object
        """
        if self.connected:
            return True, pipe

        if self.connection_started is False:
            if platform.system() == 'Windows':
                win32pipe.ConnectNamedPipe(pipe, ol)

            self.connection_started = True

        if platform.system() == 'Windows':
            r = win32event.WaitForSingleObject(ol.hEvent, 3000)
            if r == win32event.WAIT_OBJECT_0:
                self.connected = True
                self.connection_started = False
                print 'Connected'
                return True, pipe
            elif r == win32event.WAIT_TIMEOUT:
                print 'Connection attempt timed out'
                return False, pipe
            else:
                print 'Fail to connect'
                return False, pipe
        else:
            try:
                pipe = os.open(self.pipe_path, os.O_RDONLY | os.O_NONBLOCK)
            except OSError:
                return False, None
            else:
                self.connected = True
                self.connection_started = False
                return True, pipe

    def __init__(self, serial_port='COM4', from_user=r'\\.\pipe\ardupipe', to_user=None, to_user_dir=None,
        serial_timeout=0.01, baud_rate=9600):
        """Initialize a new Chatter.

        `serial_port` : where the device is located
        `from_user` : name of pipe to use to collect user's input
        `to_user` : name of file to print information from the device
            If None, autonames with the datetime
            If `to_user_dir` is not None, puts in that directory
        """
        ## Set up TO_DEV
        # Read from this pipe whenever something writes to it, and send
        # to device
        # Begin by deleting any existing FIFO, which should prevent stale
        # data from coming through.

        print "Entered __init__"

        if os.path.exists(from_user):
            os.remove(from_user)

        self.shutdown = True
        self.connected = False
        self.connection_started = False

        # pipe_name = from_user
        self.pipe_path = from_user  #os.path.join(pipe_dir, pipe_name)

        self.shutdown = False
        pipe, ol = self._create_pipe()
        connected, self.pipein = self._connect_pipe(pipe, ol)
        #    os.mkfifo(from_user)  # unix operation only
        #    self.pipein = os.open(from_user, os.O_RDONLY | os.O_NONBLOCK)
        
        ## Set up FROM_DEV
        # where to put stuff from the device
        if to_user is None:
            to_user = 'ardulines.' + \
                datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            if to_user_dir is not None:
                to_user = os.path.join(
                    os.path.realpath(to_user_dir), to_user)
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
        # actually, the chatter still picks up leftover input
        # that was echoed to TO_DEV, even with flushInput() above.
        # uncommenting the below lines doesn't seem to do anything.
        #~ self.ser.flush()
        #~ self.ser.flushOutput()
        
        self.new_user_text = ''
        self.new_device_lines = []
        
        # Check for acknowledged lines
        self.last_sent_line = None
        self.last_sent_line_acknowledged = True
        self.queued_writes = []

    def update(self, echo_to_stdout=True):
        """Called repeatedly to deal with inputs and outputs
        
        * Reads any user text on the pipe and writes to device
        * Reads any lines from the devices and writes to output file
        * Optionally echos to stdout
        * Checks whether the last sent command was acknowledged
        * If it was acknowledged, then sends top of queued_writes
        
        Right now there is a bug in which the Arduino can write text so quickly
        that this function will get stuck at reading from devices. Need some
        kind of maximum read size check for this. Alternatively, insert delays
        in the Arduino loop function.
        """
        
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
        
        # Check whether last_sent_command was acknowledged
        # Note that we always write to device (potentially setting
        # last_sent_line) before we read from device (potentially receiving
        # an acknowledgement).
        if not self.last_sent_line_acknowledged:
            for line in self.new_device_lines:
                # Any line ending with "ACK %s" % self.last_sent_line qualifies
                # This accounts for the time at the beginning.
                # Should probably separate this logic somehow.
                if line.strip().endswith('ACK ' + self.last_sent_line):
                    self.last_sent_line_acknowledged = True
        
        # Send a queued write if ready
        if self.last_sent_line_acknowledged and len(self.queued_writes) > 0:            
            self.write_to_device(self.queued_writes.pop(0))

    def close(self):
        self.ser.close()
        self.ofi.close()
        #pipein.close()
    
    def queued_write_to_device(self, s):
        """Adds the string `s` to the write queue.

        These queued strings are written to the device one at a time
        during `update` calls, and we wait for an acknowledgement before
        sending the next one.
        """
        self.queued_writes.append(s)
    
    def write_to_device(self, s, auto_newline=True):
        """Write a line to the device.
        
        Adds a newline character automatically if necessary.
        Does not call update.
        Caches string to last_sent_line.
        """
        self.last_sent_line = s 
        self.last_sent_line_acknowledged = False
        
        if auto_newline and not s.endswith('\n'):
            s = s + '\n'
        write_to_device(self.ser, s)


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


# Test this by creating an object of type chatter
objChatter = Chatter()
loop_till_interrupt(objChatter)
