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

This script should be located in the MultiSens protocol directory of the local ArduFSM repository, which should in turn be located in the host PC's Arduino sketchbook folder. In addition to this file, the MultiSens directory must also contain the following files:

1. MultiSens.ino
2. States.h
3. States.cpp

In addition, the host PC's Arduino sketchbook library must contain the following libraries:

1. chat, available at https://github.com/cxrodgers/ArduFSM/tree/master/libraries/chat
2. TimedState, available at https://github.com/cxrodgers/ArduFSM/tree/master/libraries/TimedState
3. devices, available at https://github.com/danieldkato/devices

The host PC's Python directory must include the pySerial module, which is documented at pythonhosted.org/pyserial/pyserial.html. The baud rates specified by this script and the Arduino-side code must agree.

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

Last updated DDK 2017-08-02


########################################################################
"""
# Import statements:
import chat
import time
import random
random.seed()


#########################################################################
# Define some general trial timing parameters (in seconds):    
stimDur = 2 
responseWindow = 0 
minITI = 3 # let's make this slightly longer than the Arduino's ITI to be safe
maxITI = 6 


#########################################################################
# Define the different stimulus conditions by their STPRIDX and SPKRIDX values:

paramAbbrevs = ['STPRIDX', 'SPKRIDX'] 

condition1 = [ 1, 1 ] # STPRIDX will be 1, SPKRIDX will be 1, i.e. stepper & tone 1
condition2 = [ 0, 0 ] # STPRIDX will be 0, SPKRIDX will be 0, i.e. neither stepper nor speaker
condition3 = [ 1, 0 ] # STPRIDX will be 1, SPKRIDX will be 0, i.e. tone 1 only
condition4 = [ 0, 1 ] # STPRIDX will be 0, SPKRIDX will be 1, i.e. stepper only
condition5 = [ 0, 2 ] # STPRIDX will be 0, SPKRIDX will be 2, i.e. tone 2 only
condition6 = [ 1, 2 ] # STPRIDX will be 1, SPKRIDX will be 2, i.e. stepper & tone 2


#########################################################################
# Define each phase of the experiment:

phase1 = {
	'conditions': [condition4, condition5], 
	'trialsPerCond': 100,
	'trials': []
}

phase2 = {
	'conditions': [condition1],
	'trialsPerCond': 10,
	'trials': []
}

# phase 3 will consist of the same number and types of trials as phase 1:
phase3 = phase1

# arrange all phases into a list representing the whole experiment
experiment = [phase1]

#each phase will be represented by a list of trials, each of which will in turn will be represented by a pair (STPRIDX and SPKRIDX) of parameters, different specific values of which we have already assigned to condition1, condition2, etc...
for phase in experiment:
	for condition in phase['conditions']:
		for t in range(1, phase['trialsPerCond']+1):
			phase['trials'].append(condition)

# shuffle trial order:
for phase in experiment:
	random.shuffle(phase['trials'])

#random.shuffle(phase3)


#########################################################################
# Establish serial connection with Arduino:

#We'll communicate with the Arduino by instantiating a Chatter object, writing all instructions to the Chatter object's input pipe, then calling  Chatter.update() to send the data from the input pipe to the Arduino; Chatter.update() will also write any acknowledgements sent back from the Arduino to an ardulines file saved to disk.
chtr = chat.Chatter(serial_port='COM3', baud_rate=115200)


#########################################################################
# Iterate through every phase of the experiment:

for phase in experiment: 
    for trial in phase['trials']:
    
        for i, parameter in enumerate(paramAbbrevs):
            line = 'SET ' + parameter + ' ' + str(trial[i]) + '\n' 
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