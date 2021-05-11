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

Last updated DDK 2021-05-10


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




def define_timing_params(timing_assumptions):
    """
    Load and compute stimulus-timing related parameters.

    
    Parameters:
    -----------
    timing_assumptions: str
        Path to .json file defining following keys:
            
            whisker_2_s1_latency_ms: float
                Latency between whisker contact and S1 response onset; estimate from literature.
                
            sepaker_2_s1_latency_ms: float
                Latency between speaker onset and S1 subthreshold response onset; estimated from Medini et al 2012. 
                
            stepper_on_2_whisker_latency_ms: float
                Latency between stepper onset and whisker contact. Estimate using empirical measurements.
                
            tgt_som_minus_aud_ms: float
                Desired latency between S1 auditory response onset and S1 tactile response onset. Positive values mean tactile responses should begin after                             
                auditory responses; negative values mean tactile responses should begin before auditory responses.
  
            stim_dur: float
                Un-adjusted stimulus duration, in seconds.
                
    Returns:
    --------
    timing_params: dict
        Dict defining various timing paramters. Defines all fields in Parameters, in addition to:
            
            stimDurAdjusted: float
                Adjusted stimulus duration, in seconds. Equal to un-adjusted stimulus duration plus time it takes for pole to reach whiskers. In other      
                words, gives the total amount of time between when the steper starts moving and when it's retracted.
      
            stpr_minus_spkr_ms: float
                Latency between stepper onset and speaker onset in milliseconds required to achieve desired latency between auditory and tactile response 
                onsets. Positive values mean the stepper should come on before the speaker; negative values mean the stepper should come on after the 
                speaker.
    """
    timing_params = dict()

    # Define some timing parameters used to determine how to set the latency between the stepper onset and speaker onset:    
    whisker_2_s1_ms = timing_assumptions['whisker_2_s1_latency_ms']
    spkr_2_s1_ms = timing_assumptions['speaker_2_s1_latency_ms']
    stpr_2_whisker_ms = timing_assumptions['stepper_on_2_whisker_latency_ms'] 
    tgt_som_minus_aud_ms = timing_assumptions['tgt_som_minus_aud_ms']
    stimDur = timing_assumptions['stimDur']
    
    # Print some debug messages confirming assumptions about timing. 
    print('Assuming latency between stepper onset and whisker contact is ' + str(stpr_2_whisker_ms) + ' ms.')
    print('Assuming latency between whisker contact and S1 response onset is ' + str(whisker_2_s1_ms) + ' ms.')
    print('Assuming latency between speaker onset and S1 response onset is ' + str(spkr_2_s1_ms) + ' ms.')
    print('Time of S1 whisker response onset minus time of S1 auditory response onset should be ' + str(tgt_som_minus_aud_ms) + ' ms.')
    
    # Calculate the latency between when the stepper comes on and when the speaker comes on:
    spkr_minus_stpr_ms = stpr_2_whisker_ms + whisker_2_s1_ms - spkr_2_s1_ms - tgt_som_minus_aud_ms
    stpr_minus_spkr_ms = -1 * spkr_minus_stpr_ms
    
    # Calculate the appropriate duration to make the auditory stimulus in order to ensure that the auditory stimulus ends at the same time the stepper is retracting:
    spkr_dur_s = stimDur + (stpr_2_whisker_ms - spkr_minus_stpr_ms)/1000.0
    
    # Adjust the stimulus duration to account for the amount of time it takes for the stepper to reach the whsikers:
    stimDurAdjusted = stimDur +  stpr_2_whisker_ms/1000.0
    
    # If the speaker must come on AFTER the stepper starts moving in order to achieve the desired latency between auditory and somatosensory signals arriving in S1, then instruct the user to set the appropriate delay in HardWareTriggeredNoise_dk.vi.
    if spkr_minus_stpr_ms >= 0:
        print('Speaker should turn on ' + str(spkr_minus_stpr_ms) + ' ms after stepper onset.')
        cont = raw_input('Please ensure that ''onset delay'' is set to %d ms and ''sound duration'' is set to %.3f s in HardwareTriggeredNoise_dk.vi . (Press any key to continue) ' % (spkr_minus_stpr_ms, spkr_dur_s))
    else: 
        print('Speaker should turn on ' + str(-1 * spkr_minus_stpr_ms) + ' ms before stepper onset.')
        cont = raw_input('Please ensure that ''onset delay'' is set to 0 ms and sound duration'' is set to %.3f s in HardwareTriggeredNoise_dk.vi . (Press any key to continue) ' % (spkr_dur_s))

    timing_params['whisker_2_s1_latency_ms'] = whisker_2_s1_ms
    timing_params['speaker_2_s1_latency_ms'] = spkr_2_s1_ms
    timing_params['stepper_on_2_whisker_latency_ms'] = stpr_2_whisker_ms
    timing_params['stimDurAdjusted'] = stimDurAdjusted
    timing_params['stpr_minus_spkr_ms'] = stpr_minus_spkr_ms

    return timing_params
    


def get_src_metadata():
    """
    Get metadata for source files run during experiment, including file paths and most recent commit hash. *Must be run from directory containing code to 
    be run*.
    
    
    Parameters:
    -----------
    None
    
    
    Returns:
    --------
    src_metadata: dict
        Dict containing metadata about code run during experiment. Defines following keys:
            
            srcDicts: list
                List of dicts containing git version information for files in main sketch directory. Each dict contains information about a single file, 
                including the following keys:
                    
                    path: str
                        Full path to source file.
                        
                    SHA1: str
                        SHA1 checksum of source file.
                    
            libDicts: list
                List of dicts containing version information about any Arduino libraries included in sketch code. Each element corresponds to a single 
                library. Each dict defines the following keys:
                
                    libPath: str
                        Full path to Arduino library.
                        
                    SHA1: str
                        SHA1 checksum of Arduino library.
                        
                    warnings: str
                        Any warnings that were raised in trying to get SHA1 checksum of Arduino library.                
    """
    
    src_metadata = dict()
    
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
    src_metadata['srcFiles'] =srcDicts

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
            
    src_metadata['libraries'] = libDicts
    
    return src_metadata
    
    

def define_expt_structure(settings):
    """
    Define a dict specifying the parameters of each trial in the session.
    
    Parameters:
    -----------
    Settings: dict
        Dict containing various experiment parameters. 
        
        
    Returns:
    --------
    experiment: dict
        Dict specifying parameters of each trial in the session. Defines the following keys:
            
            phases: list
                List of dicts. Each dict corresponds to a different phase of the session. Each defines the following keys:
                    
                    trials: list
                        Another list of dicts. Here each dict corresponds to a single trial. Each dict corresponding to a single trial defines keys 
                        corresponding to different trial parameters (e.g., "STPRIDX", "SPKRIDX"). In any given session, these will depend on the parameters 
                        specified in the .json settings file passed to main().
    """
    # Define experiment structure:        
    stimDurAdjusted = settings['stimDurAdjusted']
    stpr_minus_spkr_ms = settings['stpr_minus_spkr_ms']
    
    experiment = copy.deepcopy(settings['Phases'])  # Extract the experiment structure data from the dict object:
    all_trials = []
    
    # Each phase will be represented by a list of trials. Each trial will be a list of pairs. Each pair is a parameter name followed by the corresponding parameter value:
    for phase in experiment:
            phase['trials'] = []
            for condition in phase['conditions']:
                    condition["STIMDUR"] = stimDurAdjusted * 1000;
                    
                    # If the speaker needs to come on after the stepper, then don't make States.cpp call delay() between calling trigger_audio() and trigger_stepper(); HardwareTriggeredNoise_dk.vi will be responsible for implementing a delay before the speaker comes on
                    if stpr_minus_spkr_ms < 0:
                        condition["ISL"] = 0
                    
                    # If the stepper needs to come on after the stepper, then make States.cpp call delay() for the appropriate amount of time between calling trigger_audio() and trigger_stepper()
                    else:
                        condition["ISL"] = stpr_minus_spkr_ms 
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
    
    return experiment



def main():
    """
    Main function for running a single session of MultiSens experiment.
    
    
    Parameters:
    -----------
    None, but see general remarks at top of document for description of required settings files.
    
    
    Returns:
    --------
    None. 
    
    """
    baseDir = os.getcwd()
    
    # Prompt user for name of settings file to use:
    settings_file = raw_input("Please enter name of settings file to use for current session: ")
    if not os.path.isfile(settings_file):
        raise IOError('Requested settings file not found. Please ensure that settings file name was specified correctly.')
    
    # Load settings from settings.json into Python dict object:
    with open(settings_file) as json_data:
            settings = json.load(json_data)
            
    # Extract some some timing parameters that need to be used by main function:    
    stimDur= settings['StimDur_s']
    responseWindow = settings['ResponseWindow_s']
    minITI = settings['MinITI_s'] # should be slightly longer than the Arduino's ITI to be safe
    maxITI = settings['MaxITI_s']  

    # Load various timing assumptions, compute some additonal timing parameters:
    timing_file = "C:\\Users\\lab\\Documents\\Arduino\\ArduFSM\\MultiSens\\timing_assumptions.json"
    with open(timing_file) as json_data:
            timing_assumptions = json.load(json_data)
    timing_assumptions['tgt_som_minus_aud_ms'] = settings['tgt_som_minus_aud_ms']
    timing_assumptions['stimDur'] = stimDur 
    timing_params = define_timing_params(timing_assumptions)
    settings['Hostname'] = socket.gethostname()
    settings['Date'] = time.strftime("%Y-%m-%d")
    settings['whisker_2_s1_ms'] = timing_params['whisker_2_s1_latency_ms']
    settings['spkr_2_s1_ms'] = timing_params['speaker_2_s1_latency_ms']
    settings['stpr_2_whisker_ms'] = timing_params['stepper_on_2_whisker_latency_ms']
    settings['stimDurAdjusted'] = timing_params['stimDurAdjusted']
    settings['stpr_minus_spkr_ms'] = timing_params['stpr_minus_spkr_ms']

    # Get commit metadata for various source files:
    src_metadata = get_src_metadata()
    settings['libraries'] = src_metadata['libraries']
    settings['srcFiles'] = src_metadata['srcFiles']

    # Define experiment structure:
    experiment = define_expt_structure(settings)
    
    # Establish serial connection with Arduino;  we'll communicate with the Arduino by instantiating a Chatter object, writing all instructions to the Chatter object's input pipe, then calling  Chatter.update() to send the data from the input pipe to the Arduino; Chatter.update() will also write any acknowledgements sent back from the Arduino to an ardulines file saved to disk.
    os.chdir(baseDir)
    chtr = chat.Chatter(serial_port=settings['SerialPort'], baud_rate=settings['BaudRate'], serial_timeout=0.03)
    
    # Save serial communication start time to settings:
    settings['SerialStartTime'] = time.strftime("%H:%M:%S")
    
    # Save to secondary storage:
    with open('metadata.json', 'w') as fp:
            json.dump(settings, fp, indent=4)
    
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
                                if key in line and not ack:
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



if __name__ == '__main__':
    main()