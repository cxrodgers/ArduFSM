# Read from pipe and move accordingly

import serial
import time
import numpy as np
import math
import ArduFSM.chat
import os
import datetime

MANIPULATOR_PIPE = '/home/chris/dev/ArduFSM/manipulator_pipe'
UPDATE_INTERVAL = .1
now_string = datetime.datetime.now().strftime('%Y%m%d%H%M%S')

LOGNAME = '/home/chris/manipulator_log/manipulator_log.{}'.format(now_string)

def double_print(string):
    print(string)
    logfile.write(string + '\n')
    logfile.flush()

def goto(pos):
    return "ABS {} {} {}\r".format(pos[0], pos[1], pos[2])

## Define positions
# X: ML, with more positive being more lateral
# Y: AP, with more positive being more posterior
positions = {
    #~ 'C1': np.array([-15493,  2171, 75871]),
    #~ 'C3': np.array([-10861, -3516, 72592]),
    'C1': np.array([36474, 127667, 28514]),
    'C3': np.array([40378, 120979, 25666]),
}

# The "up" positions directly above
UPWARDS = 10000
positions['C1up'] = positions['C1'].copy()
positions['C1up'][2] += UPWARDS
positions['C3up'] = positions['C3'].copy()
positions['C3up'][2] += UPWARDS

# The "interpos", directly between
positions['interpos'] = (
    ((positions['C1up'] + positions['C3up']) / 2)
    .astype(np.int))


## Set up the pipe
try:
    os.remove(MANIPULATOR_PIPE)
except OSError:
    pass
os.mkfifo(MANIPULATOR_PIPE)
pipein = os.open(MANIPULATOR_PIPE, os.O_RDONLY | os.O_NONBLOCK)


## Loop function
def run_loop():
    leftover_instructions = ''
    while True:
        ## Read anything on pipein
        instructions = ArduFSM.chat.read_from_user(pipein)
        
        if instructions is not None and instructions != '':
            # Split into lines
            instructions_by_line = instructions.split('\n')
            
            # Prepend leftovers to the first instruction, if any
            if len(instructions_by_line) > 0 and len(leftover_instructions) > 0:
                double_print("leftover_update: prepending")
                instructions_by_line[0] = leftover_instructions + instructions_by_line[0]
                leftover_instructions = ''
            
            # If the last instruction doesn't end with \n, it's partial
            if not instructions.endswith('\n'):
                leftover_instructions = instructions_by_line[-1]
                instructions_by_line = instructions_by_line[:-1]
                double_print(
                    "leftover_update: setting to {}".format(
                    leftover_instructions))
            
            # Do each
            for instruction in instructions_by_line:
                # Strip and continue if nothing
                instruction = instruction.strip()
                if len(instruction) == 0:
                    continue
                
                # Print what was received
                double_print("received: {}".format(instruction))
        
                # Parse
                if instruction.startswith('goto_'):
                    ## goto action
                    # Extract target name and location
                    target_name = instruction[5:]
                    try:
                        target_loc = positions[target_name]
                    except KeyError:
                        double_print(
                            "error: unknown position: {}".format(target_name))
                        continue
                    
                    # Print what I'm about to do
                    double_print("action: going to {} at {} {} {}".format(
                        target_name, 
                        target_loc[0], target_loc[1], target_loc[2]))

                    # Now do it
                    formatted_string = goto(target_loc)
                    double_print("sending: {}".format(formatted_string))
                    moving_ser.write(formatted_string)
                    time.sleep(0.1)
                    resp = moving_ser.readline()
                    
                    # Print acknowledgement
                    double_print("acknowl: {}".format(resp))
                    
                    # Always wait after a move
                    time.sleep(0.5)
                
                elif instruction.startswith('goup'):
                    ## goup action
                    # Print what I'm about to do
                    double_print("action: going up")
                    
                    # Now do it
                    formatted_string = "RELZ %d\r" % UPWARDS
                    double_print("sending: {}".format(formatted_string))
                    moving_ser.write(formatted_string)
                    time.sleep(0.1)
                    resp = moving_ser.readline()
                    
                    # Print acknowledgement
                    double_print("acknowl: {}".format(resp))
                    
                    # Always wait after a move
                    time.sleep(0.5)
                    
                elif instruction.startswith('dbg_'):
                    # Just a debug, continue
                    continue
                else:
                    double_print("error: garbled instruction")
        
        ## Get position
        # Request position and wait for response
        ser0.write('POS\r') 
        time.sleep(0.1)
        resp0 = ser0.readline()
        
        ser1.write('POS\r') 
        time.sleep(0.1)
        resp1 = ser1.readline()

        
        ## Print position
        # Split into X, Y, Z
        # Convert to microns
        xyz0 = np.array(map(int, resp0.split())) * 0.1
        xyz1 = np.array(map(int, resp1.split())) * 0.1
        now_string = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        double_print("update: [%s] ANGL{X=%07.1f Y=%07.1f Z=%07.1f} VERT{X=%07.1f Y=%07.1f Z=%07.1f}" % (
            now_string, 
            xyz0[0], xyz0[1], xyz0[2],
            xyz1[0], xyz1[1], xyz1[2],
            ))

        
        ## update interval
        time.sleep(UPDATE_INTERVAL)


## Open connection to manipulator and keep running
with open(LOGNAME, 'w') as logfile:
    with serial.Serial('/dev/ttyUSB0', timeout=0) as ser0:
        with serial.Serial('/dev/ttyUSB1', timeout=0) as ser1:
            # Which to move
            # ser0 = angled; ser1 = vertical
            moving_ser = ser0
            
            try:
                run_loop()
            
            except KeyboardInterrupt:
                double_print("received interrupt")
                pass
            
            finally:
                os.close(pipein)
