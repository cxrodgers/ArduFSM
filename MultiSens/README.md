*Last updated DDK 6/29/16*

##OVERVIEW: 
This directory contains files needed to run the ArduFSM protocol MultiSens. This protocol is used for presenting simultaneous multi-sensory stimuli under the control of an Arduino microcontroller and records licks measured on a capacitative touch sensor. Arbitrary stimulus presentations (determined by the computer-side program) can be paired with coterminous delivery of a liquid reward, and licks during non-rewarded stimuli will result in a timeout error period. 

This readme provides documentation for the most current version of the protocol. For a record of the historical development of this protocol and more exposition of some of the design choices therein, see this directory's `devlog.md`.


##REQUIREMENTS:
This protocol directory should contain the following files:
   * `States.h`
   * `States.cpp`
   * `MultiSens.ino`
   * `testMultiSens.py`
  
The local computer's Arduino sketchbook library must contain the following libraries:
  * `chat`, available at https://github.com/cxrodgers/ArduFSM/tree/master/libraries/chat
  * `TimedState`, available at https://github.com/cxrodgers/ArduFSM/tree/master/libraries/TimedState
  * `devices`, available at https://github.com/danieldkato/devices

In addition, the path of the Python instance running `testMultiSens.py` must include the path to the module `chat`, available at https://github.com/cxrodgers/ArduFSM/blob/master/chat.py


##INSTRUCTIONS:
To run this protocol, upload `MultiSens.ino`, `States.h`, and `States.cpp` to an Arduino. Then, in a command window, navigate to this directory and enter the command:

`python testMultiSens.py`

For more specific exposition of each file, see comments in the header of each.


##DESCRIPTION

###Behavioral protocol
This protocol is used for presenting simultaneous multi-sensory stimuli under the control of an Arduino microcontroller and records licks measured on a capacitative touch sensor. Arbitrary stimulus presentations (determined by a host PC-side program) can be paired with coterminous delivery of a liquid reward, and licks during non-rewarded stimuli will result in a timeout error period. 

This protocol consists of 8 states: 
 * `WAIT_TO_START_TRIAL` 
 * `TRIAL_START` 
 * `STIM_PERIOD`
 * `RESPONSE_WINDOW` 
 * `REWARD` 
 * `POST_REWARD_PAUSE` 
 * `ERROR` 
 * `INTER_TRIAL_INTERVAL` 

During `WAIT_TO_START_TRIAL`, the Arduino does nothing until it receives the message `"RELEASE_TRL\0\n"` from the desktop. It then advances to `TRIAL_START`, when it prints the current trial parameters back to the desktop. It then advances to `STIM_PERIOD`, during which it presents the stimuli. 
 
On rewarded trials, the reward valve will open some amount of time before the end of `STIM_PERIOD`. The state will then advance to `RESPONSE_PERIOD`, during which licks will cause the state to advance to `REWARD`, during which the reward valve will open. This will be followed by a `POST_REWARD_PAUSE`, which will cycle back to `RESPONSE_WINDOW`. As long as the mouse keeps licking, this cycle will repeat until some maximum number of rewards is reached. If no licks are recorded during the response window, no further rewards are given, and the trial is scored as a miss. 

On unrewarded trials, any licks during the `STIM_PERIOD` or `RESPONSE_WINDOW` states will result in a false alarm outcome and cause the state to advance to `ERROR`. If no licks are detected during either `STIM_PERIOD` or `RESPONSE_WINDOW`, then the trial is scored as a correct reject. 
 
In any case, after the trial is scored, the state will advance to `INTER_TRIAL_INTERVAL`, during which it will report back the trial outcome, and then to `WAIT_TO_START_TRIAL`, during which it will await the parameters for the next trial and the `"RELEASE_TRL\0"` message to begin the next trial.

For a full list of trial parameters, see below. 

###Code
As with all ArduFSM protocols, the code for running this protocol consists of separate host PC-side and Arduino programs. 

####Host PC-side code
The host PC-side code is responsible for choosing and sending trial parameters to the Arduino and giving it the signal to initiate each trial (see below for detailed syntax and semantics). In this protocol, the host PC-side code is comprised entirely of `testMultiSens.py`.

In addition, the host PC-side code will save to disk a file containing all messages received back from the Arduino over the course of the experiment, including information about responses, trial outcomes and acknowledgement of trial parameters send by the computer.  

####Arduino-side code
The Arduino-side code is responsible for receiving trial parameters from the desktop, waiting to receive permission from the desktop to initiate trials, delivering stimuli, measuring responses, sending response data back to the desktop, and advancing the state. The Arduino-side code consists of three files: `MultiSens.ino`, `States.h` and `States.cpp`. 

`MultiSens.ino` is the main sketch, and defines the behavior of the Arduino on every pass of the main loop function. On every pass of the main loop, the Arduino performs the following actions: 

 1. get the current time 
 2. check for messages from the desktop 
 3. check for licks
 4. perform state-dependent operations

State-dependent operations are defined in `States.h` and `States.cpp`. These source files define functions and objects that determine how the Arduino behaves during each state, which also includes the logic for advancing states. It also defines the array where trial parameters are stored.


Unique (for the time being) to MulitSens is that `States.cpp` also instantiates a number of device objects for managing the hardware (e.g., steppers, speakers) that will be controlled by the Arduino on the current experiment. Each device instance is of a class defined in `devices.h` and `devices.cpp`. Each device class has a repertoire of behaviors that it can execute on any given trial. Each behavior has its own numeric index, and trial parameters on each trial include an index for each device, thereby specifying the behavior of every device on each trial. For a detailed description of each device class, their behaviors and a listing of indices to them, see the documentation for `devices` at https://github.com/danieldkato/devices.         

####Trial parameters
The Arduino expects to receive trial parameters with the syntax:

`"SET parameter_abbreviation parameter_value\n"`

where `parameter_abbreviation` stands for some parameter abbreviation and `parameter value` stands for the value of that parameter on the upcoming trial.

The semantics of the parameters abbreviations are as follows:
 
 * `STPRIDX`: function index for the stepper motor; used by an object representing the stepper motor to determine what actions to take during the stimulus period. 0 means do nothing, 1 means extend the stepper at the beginning of the trial. 

 * `SPKRIDX`: function index for the speaker. 0 means do nothing, 1 means play a white noise stimulus. Set to 0 by default on the Arduino. REW: whether or not the current trial will be rewarded. Set to 0 by default on the Arduino.

 * `REW_DUR`: the duration of any rewards given on the current trial. Set to 50 by default on the Arduino.

 * `IRI`: inter-reward interval; the minimum amount of time that must elapse between rewards. Set to 500 by default on the Arduino. 

 * `TO`: timeout; the minimum amount of time between a false alarm response and the following trial. Set to 6000 by default on the Arduino.

 * `ITI`: inter-trial interval; minimum amount of time between trials [?]. Set to 3000 by default on the Arduino.

 * `RWIN`: response window duration; the maximum amount of time the mouse has to respond following the stimulus. Set to 45000 by default on the Arduino.
 
 * `MRT`: maximum number of rewards mouse can receive on a single trial. Set to 1 by default on the Arduino.

 * `TOE`: terminate on error; whether or not the trial will end immediately following a false alarm response. Set to 1 by default on the Arduino. 

     

         

