/* Last updated DDK 6/7/16
 * 
 * OVERVIEW:
 * This file is the main Arduino sketch for the ArduFSM protocol MultiSens. This 
 * protocol is used for presenting simultaneous multi-sensory stimuli under the 
 * control of an Arduino microcontroller and records licks measured on a 
 * capacitative touch sensor. Arbitrary stimulus presentations (determined by a 
 * host PC-side program) can be paired with coterminous dispensation of a 
 * liquid reward , and licks during non-rewarded stimuli will result in a timeout 
 * error period.
 *  
 *  
 * REQUIREMENTS:
 * This sketch must be located in the MultiSens protocol directory within
 * a copy of the ArduFSM repository on the local computer's Arduino sketchbook
 * folder. In addition to this file, the MultiSens directory should contain
 * the following files:
 *  
 * 1. States.h
 * 2. States.cpp
 *  
 * In addition, the local computer's Arduino sketchbook library must contain 
 * the following libraries:
 *  
 * 1. chat, available at https://github.com/cxrodgers/ArduFSM/tree/master/libraries/chat
 * 2. TimedState, available at https://github.com/cxrodgers/ArduFSM/tree/master/libraries/TimedState
 * 3. devices, available at https://github.com/danieldkato/devices
 *  
 * This sketch is largely agnostic with respect to how the host PC-side code is
 * implemented; the only requirements are that both programs specify the same
 * baud rate for the serial connection, and that the host PC-side code send
 * certain specific messages comprised of byte arrays terminated by a newline
 * ('\n') character over a serial connection to the Arduino. The syntax and
 * semantics of these messages are described in this protocol's README.md.
 * 
 * 
 * INSTRUCTIONS:
 * Compile and upload this sketch along with States.h and States.cpp to an 
 * Arduino over a connected serial port. See this protocol's README.md for 
 * instructions on running the corresponding computer-side code. 
 * 
 * 
 * DESCRIPTION:
 * This main sketch is responsible for defining behavior that the Arduino should
 * repeatedly perform continuously for the duration of the experiment, defined
 * in the main `loop` function. This includes: 1) getting the current time, 2)
 * checking for messages from the computer, 3) checking for licks, and 4) 
 * performing state-dependent operations. 
 * 
 * Code for some of these state-dependent operations, is contained in this 
 * protocol's States.h and States.cpp files.  
 * 
 * Because this sketch itself does not define the state-dependent operations,
 * it should be totally protocol-independent.
 */ 



/* TODO
----
* Move the required states, like TRIAL_START and WAIT_FOR_NEXT_TRIAL,
  as well as all required variables like flag_start_trial, into TrialSpeak.cpp.
* move definitions of trial_params to header file, so can be auto-generated
* diagnostics: which state it is in on each call (or subset of calls)

Here are the things that the user should have to change for each protocol:
* Enum of states
* User-defined states in switch statement
* param_abbrevs, param_values, tpidx_*, N_TRIAL_PARAMS
*/
#include "chat.h"
//#include <Wire.h> // also for mpr121
#include <Stepper.h>
#include "TimedState.h"
#include "States.h"

extern char* param_abbrevs[N_TRIAL_PARAMS];
extern long param_values[N_TRIAL_PARAMS];
extern bool param_report_ET[N_TRIAL_PARAMS];
extern char* results_abbrevs[N_TRIAL_RESULTS];
extern long results_values[N_TRIAL_RESULTS];
extern long default_results_values[N_TRIAL_RESULTS];

//// Miscellaneous globals
// flag to remember whether we've received the start next trial signal
// currently being used in both setup() and loop() so it can't be staticked
bool flag_start_trial = 0;


//// Declarations
int take_action(char *protocol_cmd, char *argument1, char *argument2);


//// User-defined variables, etc, go here
/// these should all be staticked into loop()
STATE_TYPE next_state; 

// touched monitor
boolean sticky_licking = 0;

/// not sure how to static these since they are needed by both loop and setup

//// Setup function
void setup()
{
  unsigned long time = millis();
  int status = 1;
  
  Serial.begin(115200);
  Serial.print(time);
  Serial.println(" DBG begin setup");
  
  // random number seed
  randomSeed(analogRead(3));
  
  //// Run communications until we've received all setup info
  // Later make this a new flag. For now wait for first trial release.
  while (!flag_start_trial)
  {
    status = communications(time);
    if (status != 0)
    {
      Serial.println("comm error in setup");
      delay(1000);
    }
  }
}



//// Loop function
void loop()
{ /* Called over and over again. On each call, the behavior is determined
     by the current state.
  */
  
  //// Variable declarations
  // get the current time as early as possible in this function
  unsigned long time = millis();

  // statics 
  // these are just "declared" here, they can be modified at the beginning
  // of each trial
  static STATE_TYPE current_state = WAIT_TO_START_TRIAL;

  // The next state, by default the same as the current state
  next_state = current_state;
    
  
  // misc
  int status = 1;
  
  //// User protocol variables
  boolean licking = 0;
  
  
  //// Run communications
  status = communications(time);
  
  
  //// User protocol code
  // could put other user-specified every_loop() stuff here
  
  // Poll touch inputs
  licking = checkLicks();
  
  // announce sticky
  if (licking != sticky_licking)
  {
    Serial.print(time);
    Serial.print(" LCK ");
    sticky_licking = licking;
  }  
  
  stateDependentOperations(current_state, time);
  
  //// Update the state variable
  if (next_state != current_state)
  {
      
    Serial.print(time);
    Serial.print(" ST_CHG ");
    Serial.print(current_state);
    Serial.print(" ");
    Serial.println(next_state);
    
    Serial.print(millis());
    Serial.print(" ST_CHG2 ");
    Serial.print(current_state);
    Serial.print(" ");
    Serial.println(next_state);
  }
  current_state = next_state;
  
  return;
}


//// Take protocol action based on user command (ie, setting variable)
int take_action(char *protocol_cmd, char *argument1, char *argument2)
{ /* Protocol action.
  
  Currently two possible actions:
    if protocol_cmd == 'SET':
      argument1 is the variable name. argument2 is the data.
    if protocol_cmd == 'ACT':
      argument1 is converted into a function based on a dispatch table.
        REWARD_L : reward the left valve
        REWARD_R : reward the right valve
        REWARD : reward the current valve

  This logic could be incorporated in TrialSpeak, but we would need to provide
  the abbreviation, full name, datatype, and optional handling logic for
  each possible variable. So it seems to make more sense here.
  
  Return values:
  0 - command parsed successfully
  2 - unimplemented protocol_cmd
  4 - unknown variable on SET command
  5 - data conversion error
  6 - unknown asynchronous action
  */
  int status;
  
  //~ Serial.print("DBG take_action ");
  //~ Serial.print(protocol_cmd);
  //~ Serial.print("-");
  //~ Serial.print(argument1);
  //~ Serial.print("-");
  //~ Serial.println(argument2);
  
  if (strncmp(protocol_cmd, "SET\0", 4) == 0)
  {
    // Find index into param_abbrevs
    int idx = -1;
    for (int i=0; i < N_TRIAL_PARAMS; i++)
    {
      if (strcmp(param_abbrevs[i], argument1) == 0)
      {
        idx = i;
        break;
      }
    }
    
    // Error if not found, otherwise set
    if (idx == -1)
    {
      Serial.print("ERR param not found ");
      Serial.println(argument1);
      return 4;
    }
    else
    {
      // Convert to int
      status = safe_int_convert(argument2, param_values[idx]);

      // Debug
      //~ Serial.print("DBG setting var ");
      //~ Serial.print(idx);
      //~ Serial.print(" to ");
      //~ Serial.println(argument2);

      // Error report
      if (status != 0)
      {
        Serial.println("ERR can't set var");
        return 5;
      }
    }
  }   

  else if (strncmp(protocol_cmd, "ACT\0", 4) == 0)
  {
    // Dispatch
    return 6;
  }      
  else
  {
    // unknown command
    return 2;
  }
  return 0;
}


int safe_int_convert(char *string_data, long &variable)
{ /* Check that string_data can be converted to long before setting variable.
  
  Returns 1 if string data could not be converted to %d.
  */
  long conversion_var = 0;
  int status;
  
  // Parse into %d
  // Returns number of arguments successfully parsed
  status = sscanf(string_data, "%ld", &conversion_var);
    
  //~ Serial.print("DBG SIC ");
  //~ Serial.print(string_data);
  //~ Serial.print("-");
  //~ Serial.print(conversion_var);
  //~ Serial.print("-");
  //~ Serial.print(status);
  //~ Serial.println(".");
  
  if (status == 1) {
    // Good, we converted one variable
    variable = conversion_var;
    return 0;
  }
  else {
    // Something went wrong, probably no variables converted
    Serial.print("ERR SIC cannot parse -");
    Serial.print(string_data);
    Serial.println("-");
    return 1;
  }
}







