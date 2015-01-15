ArduFSM
=======
This repository provides code for running a behavioral training session using an Arduino. The Arduino handles the moment-to-moment trial structure and interacts directly with the hardware. The Python-side code runs on the host PC and allows the user to visualize and log the results, as well as modifying experimental parameters in real-time.

This code is part of the OpenMaze project, which provides additional hardware and software resources for behavioral experiments.
http://www.openmaze.org

Currently, each subfolder contains a different type of task. The most useful one is "TwoChoice_v2" which implements a two-alternative choice behavioral paradigm. The other subfolders contain simpler tasks which are mainly useful for debugging. Some code is shared between all tasks and is stored in the root folder.

The Arduino and the host PC communicate with each other using a Chatter object that logs all correspondence and deals with relaying messages between the two. The Arduino relies on the host PC to provide the parameters for each trial. The reason for this is that it is typically easier to write Python code to set parameters intelligently rather than Arduino code.

Each task is implements using a "finite-state machine" philosophy. Basically, at each point in time, the Arduino is in a particular state, such as "move motor". This determines how the output pins are set, and how the Arduino reacts to inputs. Some inputs can cause a state transition to a new state, such as "wait for behavioral response".

Within ./TwoChoice_v2/ you can find the following Arduino files:
  * TwoChoice_v2.ino - The Arduino sketch. This implements the two-alternative choice structure. The goal is for this     sketch to be agnostic about the exact hardware details of any particular 2AC variant.
  * hwconstants.h - Specific hardware constants for each rig, such as pin numbers
  * States.cpp, States.h - Arduino code implementing one specific 2AC task that we are using in our lab. This would      be the file to change to create a new task.
  * TimedState.cpp, TimedState.h - Base object inherited by States
  * chat.cpp, chat.h - Arduino code for chatting with the host PC
  * mpr121.cpp, mpr121.h - For interacting withe mpr121 lick detector

There are also the following Python files:
  * main.py - The main user-level script to run when starting a new session
  * ../chat2.py - Implements the Chatter object which deals with communicating with the Arduino. You can use just      this object without using any of the other behavioral code if you wanted to redesign the rest of it.
  * TrialSpeak.py - Implements the communication protocol used by Chatter
  * trial_setter2.py - Chooses the parameters of the next trial, based on the log of the previous trials
  * trial_plot2.py - Plots the experiment progress

During early stages of development, I discussed many of the design considerations in further detail here:
http://python-arduino-statemachine.blogspot.com/

However this page has been superceded by the OpenMaze project:
http://www.openmaze.org
Please visit OpenMaze to ask questions or make suggestions!
