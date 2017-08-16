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
			{"STPRIDX":1, "SPKRIDX":0}
			{"STPRIDX":0, "SPKRIDX":1}
			{"STPRIDX":0, "SPKRIDX":2}
			{"STPRIDX":1, "SPKRIDX":1}
			{"STPRIDX":1, "SPKRIDX":2}
			],
	"trialsPerCond": 10},
	{"conditions":[ 
			{"STPRIDX":1, "SPKRIDX":1}
			],
	"trialsPerCond": 300},
	{"conditions":[ 
			{"STPRIDX":1, "SPKRIDX":0}
			{"STPRIDX":0, "SPKRIDX":1}
			{"STPRIDX":0, "SPKRIDX":2}
			{"STPRIDX":1, "SPKRIDX":1}
			{"STPRIDX":1, "SPKRIDX":2}
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
import subprocess
random.seed()


#########################################################################
# Load settings from settings.json into Python dict object:
with open('settings.json') as json_data:
	settings = json.load(json_data)
	
# Define some general trial timing parameters (in seconds):    
stimDur = settings['StimDur_s']
responseWindow = settings['ResponseWindow_s']
minITI = settings['MinITI_s'] # should be slightly longer than the Arduino's ITI to be safe
maxITI = settings['MaxITI_s']  


#########################################################################
# Get version information about host-PC-side scripts, Arduino code, and dependencies, and write to JSON file

# Find all source files in the main sketch directory:
sources = [x for x in os.listdir(os.getcwd()) if '.cpp' in x or '.h' in x or '.ino' in x or '.py' in x] 

baseDir = os.getcwd()
baseCmd = 'git log -n 1 --pretty=format:%H -- '
srcList = []
# For each source file in the main sketch directory... 
for s in sources:
	
	# ... get  its full path:
	fullPath = baseDir + '\\' + s
	
	# ... get its SHA1 hash:
	fullCmd = baseCmd + ' -- ' + s
	proc = subprocess.Popen(fullCmd, stdout=subprocess.PIPE, shell=True)
	sha1, err = proc.communicate()
	
	if not sha1:
		sha1 = 'file not under git control'
	
	# ... put the path and SHA1 into a dict: 
	d = {"path": fullPath, "SHA1": sha1}
	srcList.append(d)

settings['srcFiles'] = srcList	
with open('metadata.json', 'w') as fp:
	json.dump(settings, fp)



#########################################################################
# Define experiment structure:
	
experiment = settings['Phases']  # Extract the experiment structure from the dict object:

# Each phase will be represented by a list of trials. Each trial will be a list of pairs. Each pair is a parameter name followed by the corresponding parameter value:
for phase in experiment:
	phase['trials'] = []
	for condition in phase['conditions']:
		for t in range(1, phase['trialsPerCond']+1):
			phase['trials'].append(condition)

# Shuffle trial order:
for phase in experiment:
	random.shuffle(phase['trials'])

#random.shuffle(phase3)


#########################################################################
# Establish serial connection with Arduino;  we'll communicate with the Arduino by instantiating a Chatter object, writing all instructions to the Chatter object's input pipe, then calling  Chatter.update() to send the data from the input pipe to the Arduino; Chatter.update() will also write any acknowledgements sent back from the Arduino to an ardulines file saved to disk.
chtr = chat.Chatter(serial_port=settings['SerialPort'], baud_rate=settings['BaudRate'])


#########################################################################
# Iterate through every phase of the experiment:

for phase in experiment: 
    for trial in phase['trials']:
    
        for key, value in trial.iteritems():
            line = 'SET ' + key + ' ' + str(value) + '\n' 
            f = open(chtr.pipein.name, 'w') #write the set trial parameter command to the chatter object's input pipe
            f.write(line)
            f.close()
            chtr.update() #write set trial parameter command from the input pipe to the Arduino, write any received messages to ardulines
        
        time.sleep(2)
        f = open(chtr.pipein.name, 'w') 
        f.write('RELEASE_TRL\n') #write the relase trial command to the chatter object's input pipe
        f.close()
        chtr.update() #write the release trial command from the input pipe to the Arduino, write any received messages to ardulines
        
        trialStart = time.time()
        while (time.time() - trialStart < stimDur + responseWindow + minITI + random.uniform(0,maxITI-minITI)):
            chtr.update()
    
chtr.close()