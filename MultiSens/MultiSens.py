"""
MultiSens.py

DOCUMENTATION TABLE OF CONTENTS:
I. OVERVIEW
II. REQUIREMENTS
III. INSTRUCTIONS
IV. DESCRIPTION

#########################################################################
I. OVERVIEW:

This file constitutes the main host PC-side Python script for the ArduFSM protocol MultiSens. This protocol is used for presenting simultaneous multi-sensory stimuli under the control of an Arduino microcontroller. It can also record licks using a capacitative touch sensor. Arbitrary stimulus presentations (determined by this host PC-side program) can be paired with coterminous dispensation of a liquid reward, and licks during non-rewarded stimuli will result in a timeout error period.

This particular instantiation of the MultiSens protocol consists of 3 phases:

Phase 1: interleaved trials of whisker stimulus alone, tone alone, and whisker stimulus plus tone
Phase 2: repeated trials of whisker plus tone
Phase 3: the same as phase 1


#########################################################################
II. REQUIREMENTS: 

1) This script should be located in the MultiSens protocol directory of the local ArduFSM repository, which should in turn be located in the host PC's Arduino sketchbook folder. In addition to this file, the MultiSens directory must also contain the following files:

        a. MultiSens.ino
        b. States.h
        c. States.cpp

2) The host PC's Arduino sketchbook library must contain the following libraries:

        a. chat, available at https://github.com/cxrodgers/ArduFSM/tree/master/libraries/chat
        b. TimedState, available at https://github.com/cxrodgers/ArduFSM/tree/master/libraries/TimedState
        c. devices, available at https://github.com/danieldkato/devices

3) The directory containing this script must contain a JSON file called 'settings.json'. This file MUST define the following attributes:

        a. "SerialPort" - the serial port used by the local Arduino installation to connect to the Arduino board
        b. "BaudRate" - the baud rate used to communicate between the host PC and the Arduino. This must match the baud rate specified in MultiSens.ino
        c. "StimDur_s" - stimulus duration, in seconds
        d. "MinITI_s" - minimum inter-trial interval, in seconds
        e. "MaxITI_s" - maximum inter-trial interval, in seconds
        f. "ResponseWindow_s" - response window duration, in seconds (can be 0)
        g. "Phases" - list of dicts defining the experiment structure. Each dict should in turn define the following attributes:
                i. "trialsPerCond" - number of trials per condition to present throughout the course of the phase
                ii. "conditions" - a list. Each element of this list is itself a dict representing a single condition to be presented throughout the course of the phase. Each element of the dict represents one parameter of the corresponding condition.
                
An example settings.json file could be as follows:

{
"BaudRate": 115200,
"SerialPort": "COM3",
"StimDur_s": 2,
"ResponseWindow_s": 0,
"MinITI_s": 3,
"MaxITI_s": 6,
"Phases": [
        {"conditions":[ 
                        {"STPRIDX":1, "SPKRIDX":0, "ISL":0}
                        {"STPRIDX":0, "SPKRIDX":1, "ISL":0}
                        {"STPRIDX":0, "SPKRIDX":2, "ISL":0}
                        {"STPRIDX":1, "SPKRIDX":1, "ISL":0}
                        {"STPRIDX":1, "SPKRIDX":2, "ISL":0}
                        ],
        "trialsPerCond": 10},
        {"conditions":[ 
                        {"STPRIDX":1, "SPKRIDX":1, "ISL":0}
                        ],
        "trialsPerCond": 300},
        {"conditions":[ 
                        {"STPRIDX":1, "SPKRIDX":0, "ISL":0}
                        {"STPRIDX":0, "SPKRIDX":1, "ISL":0}
                        {"STPRIDX":0, "SPKRIDX":2, "ISL":0}
                        {"STPRIDX":1, "SPKRIDX":1, "ISL":0}
                        {"STPRIDX":1, "SPKRIDX":2, "ISL":0}
                        ],
        "trialsPerCond": 10},
]
}

See also https://github.com/danieldkato/ArduFSM/blob/master/MultiSens/settings.json for an example settings file. 

4) The host PC's Python directory must include the pySerial module, which is documented at pythonhosted.org/pyserial/pyserial.html. The baud rates specified by this script and the Arduino-side code must agree.

If this script is not used to dynamically update timing parameters on each trial, then the timing parameters set here should match the default timing parameters set in the Arduino code. 


#########################################################################
III. INSTRUCTIONS:

Set the desired hardware and trial parameters in the lines indicated by comments. Compile and upload MultiSens.ino, States.h and States.cpp to an Arduino microcontroller. Then, run this script by either using a command window to navigate to the directory containing this script and enter:

python multiSens.py

or open this script in a text editor like SciTE and press F5.


#########################################################################
IV. DESCRIPTION:

This host PC-side script is responsible for deciding the parameters of each trial, sending them over a serial port to the Arduino microcontroller, and giving the Arduino permission to commence the subsequent trial. The trial will commence as soon as permission is received as long as the Arduino has completed the previous trial, so this script is also repsonsible for timing the permission signal appropriately. Every line sent by this script must terminate in a newline ('\n') character.

In addition, this host PC-side script listens for messages sent back from the Arduino and records them in a text file saved in the MultiSens directory. These include acknowledgements of trial parameters sent from the host PC, lick data, trial outcome data, all FSM state changes, and periodic debug statements. 

The Arduino expects each line from the host PC to follow a certain syntax and semantics. Across all (or at any rate most) protocols, the syntax for setting upcoming trial parameters should be: 

SET <parameter abbreviation> <parameter value>\n

where <parameter abbreviation> stands in for some parameter abbreviation and <parameter value> stands in for the value of that parameter on the upcoming trial. <parameter value> must be numeric or Boolean. The Arduino expects all times to be in milliseconds. 

As far as the semantics, the parameter abbreviations sent by the host PC must match the possible parameter abbreviations that the Arduino is expecting. The parameters are specific to a given protocol (because different protocols may require different parameters). For the protocol MultiSens, the parameter abbreviations are:

        STPRIDX - function index for the stepper motor; used by an object representing the stepper motor to determine what actions to take during the stimulus period. 0 means do nothing, 1 means extend the stepper at the beginning of the trial. 

        SPKRIDX - function index for the speaker. 0 means do nothing, 1 means play a white noise stimulus. Set to 0 by default on the Arduino. 

        STIMDUR - stimulus period duration. Set to 2000 by default on the Arduino.

        REW - whether or not the current trial will be rewarded. Set to 0 by default on the Arduino.

        REW_DUR - the duration of any rewards given on the current trial. Set to 50 by default on the Arduino.

        IRI - inter-reward interval; the minimum amount of time that must elapse between rewards. Set to 500 by default on the Arduino. 

        TO - timeout; the minimum amount of time between a false alarm response and the following trial. Set to 6000 by default on the Arduino.

        ITI - inter-trial interval; minimum amount of time between trials [?]. Set to 3000 by default on the Arduino.

        RWIN - response window duration; the maximum amount of time the mouse has to respond following the stimulus. Set to 45000 by default on the Arduino.

        MRT - maximum number of rewards mouse can receive on a single trial. Set to 1 by default on the Arduino.

        TOE - terminate on error; whether or not the trial will end immediately following a false alarm response. Set to 1 by default on the Arduino. 
        
        ISL - interstimulus latency, i.e., the time between tone onset and whisker stim onset (or vice-versa) on a given trial, in milliseconds. If positive, whisker stim precedes tone; if negative, tone precedes whisker stim.

Once the trial parameters are received, the Arduino will wait to begin the upcoming trial until it receives the message

RELEASE_TRL\n

Last updated DDK 2017-08-15


########################################################################
"""
# Import statements:
import chat
import time
import random
import json
import os
import sys
import subprocess
import socket
import copy
import warnings
random.seed()

############################################################################
# Define some utility functions:
def checkContinue(str):
        if str == 'n':
                sys.exit('Executiuon terminated by user.')
        elif str == 'y':
                return
        else:
                choice = raw_input('Please enter y or n.')
                checkCont(choice)
                

#########################################################################
# Prompt user for name of settings file to use:
settings_file = raw_input("Please enter name of settings file to use for current session: ")
if not os.path.isfile(settings_file):
    raise IOError('Requested settings file not found. Please ensure that settings file name was specified correctly.')

        
#########################################################################
# Load settings from settings.json into Python dict object:
with open(settings_file) as json_data:
        settings = json.load(json_data)
        
# Define some general trial timing parameters (in seconds):    
stimDur = settings['StimDur_s']
responseWindow = settings['ResponseWindow_s']
minITI = settings['MinITI_s'] # should be slightly longer than the Arduino's ITI to be safe
maxITI = settings['MaxITI_s']  


#########################################################################
# Define and save metadata to secondary storage:

settings['Hostname'] = socket.gethostname()
settings['Date'] = time.strftime("%Y-%m-%d")

# Get version information for source files in main sketch directory:
sources = [x for x in os.listdir(os.getcwd()) if ('.pyc' not in x) and ('.cpp' in x or '.h' in x or '.ino' in x or '.py' in x or '.vi' in x)]  #Find all source files in the main sketch directory:
baseDir = os.getcwd()
baseCmd = 'git log -n 1 --pretty=format:%H -- '
srcDicts = []
for s in sources:
        
        warns = []
        
        # ... get  its full path:
        fullPath = baseDir + '\\' + s
        srcDict = {"path": fullPath}
        
        # ...  try to find the SHA1 of its latest git commit:	
        fullCmd = baseCmd + ' -- ' + '"' + s + '"'
        proc2 = subprocess.Popen(fullCmd, stdout=subprocess.PIPE, shell=True)
        sha1, err = proc2.communicate()

        # ... if a SHA1 was successfully retrieved, then add it to the dict:
        if sha1:
                srcDict["SHA1"] = sha1
        # ... otherwise, output a warning that the file is not under git control and give the user a chance to abort execution
        else:
                warnTxt = s + ' not under git control. It is advised that all source code files be under git control.'
                warns.append(warnTxt)
                warnings.warn(warnTxt)		
                choice = raw_input("Proceed anyway? ([y]/n)")
                checkContinue(choice)

        # Check whether there are any uncommitted changes:
        proc = subprocess.Popen('git diff -- ' + s, stdout=subprocess.PIPE, shell=True)
        diff, err = proc.communicate()
        
        # ... if there are uncommitted changes, throw a warning and ask the user to commit or stash any changes:
        if diff:
                warnTxt = 'Uncommitted changes detected in ' + s + '. It is advised to commit or stash any changes before proceeding.'
                warns.append(warnTxt)
                warnings.warn(warnTxt)
                choice = raw_input("Proceed anyway? ([y]/n)")
                checkContinue(choice)
        
        if warns: 
                srcDict["Warnings"] = warns
        
        # ... append dictionary for current source code file to list
        srcDicts.append(srcDict)

# Write list of dicts, one for each source code file, to settings:
settings['srcFiles'] =srcDicts


# Get version information for Arduino libraries:
inos = [y for y in os.listdir(os.getcwd()) if '.ino' in y] # find all .ino files in main sketch directory 
arduinoPath = 'C:\\Program Files (x86)\\Arduino'
os.chdir(arduinoPath)
verifyCmd = 'arduino_debug -v --verify ' + '"' + baseDir + '\\' + inos[0] + '"'
print(verifyCmd)
out, err = subprocess.Popen(verifyCmd, stdout=subprocess.PIPE, shell=True).communicate() # compile the sketch using the Arduino command-line interface
out = out.splitlines() 
libLines = [z for z in out if 'Using library' in z] # find any lines in the output that start with 'Using library'
libDicts = []
for lib in libLines:
        
        warns = []
        
        # get the path of the library:
        ind = lib.find(':')
        libPath = lib[ind+2:]

        # if the line ends in '(legacy)' because it's been previously compiled, exclude '(legacy)' to isolate the path to the library
        if libPath[-len(' (legacy)'):]  == ' (legacy)':
                libPath = libPath[:-len(' (legacy)')]
        print(libPath)
        
        # get the name of the library:
        ind2 = libPath.rfind('\\')
        libName = libPath[ind2+1:]
        print(libName)
        libDict = {"libPath": libPath}
        os.chdir(libPath) # cd to the library directory
        
        # Check if the library has uncommitted changes.  This part is a bit cludgey due to the way the repos are organized. Library directories are either a) repos in their own right, or b) a sparse checkout of the full ArduFSM directory.  How to check the latest commit information differs based on which one it is. 	
        
        # If the library is a full repo in its own right:
        if 'libraries' not in os.listdir(os.getcwd()):

                # ... try to get the SHA1 of the directory's latest  git commit
                try:
                        sha1 = subprocess.check_output(['git', 'log', '-n 1', '--pretty=format:%H'], stderr=subprocess.STDOUT)
                # ... include an exception if the library isn't under git control. Maybe this should be changed to a warning?
                except subprocess.CalledProcessError as e:
                        warns.append(e.output)
                
                #  Check whether there are any uncommitted changes:
                proc = subprocess.Popen('git diff', stdout=subprocess.PIPE, shell=True)
                diff, err = proc.communicate()		
                
                # ... if there are uncommitted changes, throw a warning and ask the user to commit or stash any changes:
                if diff:
                        warnTxt = 'Uncommitted changes detected in library ' + libName + '. It is advised to commit or stash any changes before proceeding'
                        warns.append(warnTxt)
                        warnings.warn(warnTxt)
                        choice = raw_input("Proceed anyway? ([y]/n)")
                        checkContinue(choice)
                        
                        
        # If the library is a sparse checkout of ArduFSM:		
        else:
                # get the names of the .h and .cpp files in the top-level directory:
                srcFiles = [x for x in os.listdir(os.getcwd()) if '.h' in x or '.cpp' in x]
                os.chdir('libraries\\' + libName)
                
                # for each file in the top-level directory, make sure it has the same hash object as the corresponding file in the lower-level directory (that was originally pulled from the repo)
                for s in srcFiles:
                        outerSHA1 = subprocess.check_output(['git', 'hash-object', s])
                        innerSHA1 = subprocess.check_output(['git', 'hash-object', s])	

                # ... if there is a mismatch, warn the user and offer a chance to abort execution
                if outerSHA1 != innerSHA1:
                        warnTxt = 'Uncommitted changes detected in library ' + libName + '. It is advised to commit or stash any changes before proceeding'
                        warns.append(warnTxt)
                        warnings.warn(warnTxt)
                        choice = raw_input("Proceed anyway? ([y]/n)")
                        checkContinue(choice)				

                # ... if there's no mistmatch or if the user instructs the program to proceed anyway, try to get the directory's latest SHA1
                try:
                        sha1 = subprocess.check_output(['git', 'log', '-n 1', '--pretty=format:%H'], stderr=subprocess.STDOUT)
                # ... include an exception if the library isn't under git control. Maybe this should be changed to a warning?
                except subprocess.CalledProcessError as e:
                        warns.append(e.output)
        
        if sha1:
                libDict['SHA1'] = sha1
        else:
                warns.append('At least one source file in library not under git control.')
                
        if warns:
                libDict['Warnings'] = warns
                
        libDicts.append(libDict)
        
settings['libraries'] = libDicts
        
        
#########################################################################
# Define experiment structure:
        
experiment = copy.deepcopy(settings['Phases'])  # Extract the experiment structure data from the dict object:
all_trials = []

# Each phase will be represented by a list of trials. Each trial will be a list of pairs. Each pair is a parameter name followed by the corresponding parameter value:
for phase in experiment:
        phase['trials'] = []
        for condition in phase['conditions']:
                n_trials = condition['NUM_TRIALS']
                for t in range(1, n_trials+1):
                        phase['trials'].append(condition)
                        all_trials.append(condition)

# Shuffle trial order:
for phase in experiment:
        random.shuffle(phase['trials'])

#random.shuffle(phase3)
print(all_trials)
print(len(all_trials))

#########################################################################
# Establish serial connection with Arduino;  we'll communicate with the Arduino by instantiating a Chatter object, writing all instructions to the Chatter object's input pipe, then calling  Chatter.update() to send the data from the input pipe to the Arduino; Chatter.update() will also write any acknowledgements sent back from the Arduino to an ardulines file saved to disk.


os.chdir(baseDir)
chtr = chat.Chatter(serial_port=settings['SerialPort'], baud_rate=settings['BaudRate'])

# Save serial communication start time to settings:
settings['SerialStartTime'] = time.strftime("%H:%M:%S")

# Save to secondary storage:
with open('metadata.json', 'w') as fp:
        json.dump(settings, fp, indent=4)


#########################################################################
# Iterate through every phase of the experiment:

n = 0
trlp_transmission_period = 1

for phase in experiment: 
    for trial in phase['trials']:
            
        # Choose ITI:
        ITI = random.uniform(minITI, maxITI)
            
        n = n + 1
        print('trial ' + str(n))

        # Start ITI:
        start_ITI = time.time()
        
        # Transmit trial paramters:
        for key, value in trial.iteritems():
            
            #Write set trial parameter command from the input pipe to the Arduino:
            line = 'SET ' + key + ' ' + str(value) + '\n' 
            chat.write_to_device(chtr.ser, str(line))
            ack = 0
            
            #Wait for trial parameter acknowledgement from Arduino:
            while not ack:
                    newlines = chat.read_from_device(chtr.ser)
                    for line in newlines:
                            chat.write_to_user(chtr.ofi, line) # write trial parameter acknowledgement from Arduino to ardulines file
                            chat.write_to_user(sys.stdout, line)
                            sys.stdout.flush()
                            if key in line:
                                ack = 1
        
        # Wait out remainder of ITI:
        trlp_transmission_end = time.time()
        trlp_transmission_duration = trlp_transmission_end - start_ITI
        if ITI > trlp_transmission_duration:
                while (time.time() - trlp_transmission_end < ITI - trlp_transmission_duration):
                        chtr.update()
        
        #Release trial:
        f = open(chtr.pipein.name, 'w') 
        f.write('RELEASE_TRL\n') #write the relase trial command to the chatter object's input pipe
        f.close()
        chtr.update() #write the release trial command from the input pipe to the Arduino, write any received messages to ardulines
        
        # Wait out trial:
        trial_complete = 0
        while not trial_complete:
                newlines = chat.read_from_device(chtr.ser)
                for line in newlines:
                    chat.write_to_user(chtr.ofi, line) # write trial parameter acknowledgement from Arduino to ardulines file
                    chat.write_to_user(sys.stdout, line)
                    sys.stdout.flush()
                    if 'TRLR OUTC' in line:
                        trial_complete = 1                
        
        #trialStart = time.time()
        #wait_period = stimDur + responseWindow
        #while (time.time() - trialStart < wait_period):
         #   chtr.update()
    
chtr.close()
