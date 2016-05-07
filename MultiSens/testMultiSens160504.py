"""
Use this script to test the ArduFSM protocol MultiSens. Run in conjunction with an Arduino running all of the .ino, .h and .cpp files in ArduFSM/MultiSens. 

As of 160405, this program appears to work and produces output that one would reasonably expect (see testMultiSens_output160504 in this directory).

To run this program, after uploading MultiSens.ino to the Arduino, navigate to the directory containing this script in a command window an enter:

python testMultiSens.py

Python's job in the ArduFSM framework is just to send instructions to the Arduino. Specifically, it must a) send the Arduino the parameters for the upcoming trial and b) signal permission to begin executing the upcoming trial.

The Arduino is expecting each line from the computer to follow a certain syntax and semantics. Across all (or at any rate most) protocols, the syntax for setting upcoming trial parameters should be: 

SET <parameter abbreviation> <parameter value>

where <parameter abbreviation> stands in for some parameter abbreviation and <parameter value> stands in for the value of that parameter on the upcoming trial. <parameter value> must be numeric or Boolean. The Arduino expects all times to be in milliseconds. 

As far as the semantics, the parameter abbreviations sent by the computer must match the possible parameter abbreviations that the Arduino is expecting. The parameters are specific to a given protocol (because different protocols may require different parameters). For the protocol MultiSens, the parameter abbreviations are:

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

RELEASE_TRL
"""

import chat
import time

#For simplicity, let's arrange four unrewarded example trials:
#1. Stepper only
#2. Speaker only
#3. Neither stepper nor speaker
#4. Both stepper and speaker

#Since we don't want to worry about rewards or responses from a nonexistent mouse, we'll leave the default REW value of 0. Since no reward will be given, all of the other reward-related variables can be left to their default values as well. We can leave the stimulus duration to its default value of 2000 as well. This just leaves STPRIDX, SPKRIDX for us to set on each trial.  

paramAbbrevs = ['STPRIDX', 'SPKRIDX'] #parameters we'll have to set on every trial
trial1 = [ 1, 1 ] # STPRIDX will be 1, SPKRIDX will be 0, i.e. stepper only
trial2 = [ 0, 0 ] # STPRIDX will be 0, SPKRIDX will be 1, i.e. speaker only
trial3 = [ 1, 0 ] # STPRIDX will be 0, SPKRIDX will be 0, i.e. neither stepper nor speaker
trial4 = [ 0, 1 ] # STPRIDX will be 1, SPKRIDX will be 1, i.e. both stepper and speaker
experiment = [ trial1, trial2, trial3, trial4 ]

stimDur = 2
responseWindow = 3
ITI = 3 #seconds; let's make this slightly longer than the Arduino's ITI to be safe

#We'll communicate with the Arduino by instantiating a Chatter object, writing all instructions to the Chatter object's input pipe, then calling  Chatter.update() to send the data from the input pipe to the Arduino; Chatter.update() will also write any acknowledgements sent back from the Arduino to an ardulines file saved to disk.
chtr = chat.Chatter(serial_port='COM3', baud_rate=115200)

for trial in experiment: 
    
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
    while (time.time() - trialStart < stimDur + responseWindow + ITI):
        chtr.update()
    
chtr.close()