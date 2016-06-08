###OVERVIEW 160607: 
This file provides documentation for the most current version of the ArduFSM protocol MultiSens. For a record of the historical development of this protocol and more exposition of some of the design choices therein, see this directory's devlog.md.


###PROTOCOL DESCRIPTION:
This protocol is used for presenting simultaneous multi-sensory stimuli. Arbitrary stimulus presentations can be paired with coterminous dispensation of a liquid reward (determined by the computer-side program), and licks during non-rewarded stimuli will result in a timeout error period. 


###REQUIREMENTS:
This protocol directory should contain the following files:
   1. config.h
   2. config.cpp
   3. States.h
   4. States.cpp
   5. MultiSens.ino
   6. testMultiSens.py
  
Running this protocol requires that the local computer's Arduino sketchbook library contain the following libraries:
  1. chat, available at https://github.com/cxrodgers/ArduFSM/tree/master/libraries/chat
  2. devices, available at https://github.com/danieldkato/devices

In addition, the path of the Python instance running testMultiSens.py must include the path to the module `chat`, available at https://github.com/cxrodgers/ArduFSM/blob/master/chat.py


###INSTRUCTIONS:
To run this protocol, upload MultiSens.ino to an Arduino. Then, in a command window, navigate to this directory and enter the command:

`python testMultiSens.py`

For more specific exposition of each file, see comments in the header of each.

