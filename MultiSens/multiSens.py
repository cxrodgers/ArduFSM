"""
Last updated DDK 7/11/16

OVERVIEW:
This file is the main Python script for the ArduFSM protocol MultiSens. This protocol is used for presenting simultaneous multi-sensory stimuli under the control of an Arduino microcontroller. It can also record licks using a capacitative touch sensor. Arbitrary stimulus presentations (determined by this host PC-side program) can be paired with coterminous dispensation of a liquid reward , and licks during non-rewarded stimuli will result in a timeout error period.

This particular instantiation of the MultiSens protocol consists of 3 phases:

Phase 1: interleaved trials of whisker stimulus alone, tone alone, and whisker stimulus plus tone
Phase 2: repeated trials of whisker plus tone
Phase 3: the same as phase 1


REQUIREMENTS: 
This script should be located in the MultiSens protocol directory of the ArduFSM repository, which should in turn be located in the local system's Arduino sketchbook folder. In addition to this file, the MultiSens directory must also contain the following files:

1. MultiSens.ino
2. States.h
3. States.cpp

In addition, the local system's Arduino sketchbook library must contain the following libraries:

1. chat, available at https://github.com/cxrodgers/ArduFSM/tree/master/libraries/chat
2. TimedState, available at https://github.com/cxrodgers/ArduFSM/tree/master/libraries/TimedState
3. devices, available at https://github.com/danieldkato/devices

The local system's Python directory must include the pySerial module, which is documented at pythonhosted.org/pyserial/pyserial.html. The baud rates specified by this script and the Arduino-side code must agree.

If this script is not used to dynamically update timing parameters on each trial, then the timing parameters set here should match the default timing parameters set in the Arduino code. 


INSTRUCTIONS:
Set the desired hardware and trial parameters in the lines indicated by comments. Compile and upload MultiSens.ino, States.h and States.cpp to an Arduino microcontroller. Then, run this script by either using a command window to navigate to the directory containing this script and enter:

python multiSens.py

or open this script in a text editor like SciTE and press F5.


DESCRIPTION:
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
"""

import chat
import time
import random
random.seed()

#set general trial timing parameters; we don't need to change these from trial to trial for this protocol
stimDur = 2
responseWindow = 3
minITI = 3 #seconds; let's make this slightly longer than the Arduino's ITI to be safe
maxITI = 6

#Since we are not giving reward in this experiment and we are not changing the trial timing parameters, the only parameters we have to set on each trial are what the stepper does and what the speaker does, i.e. STPRIDX and SPKRIDX.  
paramAbbrevs = ['STPRIDX', 'SPKRIDX'] 

#define the different stimulus conditions by their STPRIDX and SPKRIDX values:
condition1 = [ 1, 1 ] # STPRIDX will be 1, SPKRIDX will be 1, i.e. both stepper and speaker
condition2 = [ 0, 0 ] # STPRIDX will be 0, SPKRIDX will be 0, i.e. neither stepper nor speaker
condition3 = [ 1, 0 ] # STPRIDX will be 0, SPKRIDX will be 1, i.e. speaker only
condition4 = [ 0, 1 ] # STPRIDX will be 1, SPKRIDX will be 0, i.e. stepper only

#set the trials per condition for each phase (phase 3 is identical to phase1, so we need not set its parameters explicity)
p1trialsPerStim = 30
p2trialsPerStim = 100

#each phase will be represented by a list of trials, each of which will in turn will be represented by a pair (STPRIDX and SPKRIDX) of parameters, different specific values of which we have already assigned to condition1, condition2, etc...
phase1 = []
phase2 =[]

#populate the lists representing phases
for i in range(1,p1trialsPerStim):
    phase1.append(condition1)
    phase1.append(condition3)
    phase1.append(condition4)

for j in range(1,p2trialsPerStim):
    phase2.append(condition1)
    
#phase 3 will consist of the same number and types of trials as phase 1
phase3 = phase1

#shuffle the trial order of the phases (1 and 3 only - phase 2 consists of all the same condition, so it doesn't matter)
random.shuffle(phase1)
random.shuffle(phase3)

#arrange all phases into an appropriately ordered list representing the trial structure of the whole experiment
experiment = [phase1, phase2, phase3]

#We'll communicate with the Arduino by instantiating a Chatter object, writing all instructions to the Chatter object's input pipe, then calling  Chatter.update() to send the data from the input pipe to the Arduino; Chatter.update() will also write any acknowledgements sent back from the Arduino to an ardulines file saved to disk.
chtr = chat.Chatter(serial_port='COM9', baud_rate=115200)

#iterate through every phase of the experiment
for phase in experiment: 
    for trial in phase:
    
        for i, parameter in enumerate(paramAbbrevs):
            line = 'SET ' + parameter + ' ' + str(trial[i]) + '\n' 
            f = open(chtr.pipein.name, 'w') #write the set trial parameter command to the chatter object's input pipe
            f.write(line)
            f.close()
            chtr.update() #write set trial parameter command from the input pipe to the Arduino, write any received messages to ardulines
        
        f = open(chtr.pipein.name, 'w') 
        f.write('RELEASE_TRL\n') #write the relase trial command to the chatter object's input pipe
        f.close()
        chtr.update() #write the release trial command from the input pipe to the Arduino, write any received messages to ardulines
        
        trialStart = time.time()
        while (time.time() - trialStart < stimDur + responseWindow + minITI + random.uniform(0,maxITI-minITI)):
            chtr.update()
    
chtr.close()