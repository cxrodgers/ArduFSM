/* Simple protocol to test the setting of trial parameters.

The inter-trial interval can be set. On each trial, the arduino waits this
long, and then proceeds. The trial release signal but be received before
it can begin the next trial.

TODO
----
* Separate the trial protocol specific code, like setting parameters,
from general TrialSpeak parsing code in chat.cpp
* Move the required states, like TRIAL_START and WAIT_FOR_NEXT_TRIAL,
  into chat.cpp.
* Some standard way to create waiting states.
* Think about fixing the variables at the beginning of each trial.


Here are the things that the user should have to change for each protocol:
* Enum of states
* User-defined states in switch statement
* trial_params

*/
#include "chat.h"


//// States
// Defines the finite state machine for this protocol
enum STATE_TYPE
{
  TRIAL_START,
  INTER_TRIAL_INTERVAL,
  WAIT_FOR_NEXT_TRIAL
} current_state = TRIAL_START;


//// Global trial parameters structure. This holds the current value of
// all parameters. Should probably also make a copy to hold the latched
// values on each trial.
TRIAL_PARAMS_TYPE trial_params;


//// Miscellaneous globals
// Debugging announcements
unsigned long speak_at = 1000;
unsigned long interval = 1000;

// flag to remember whether we've received the start next trial signal
bool flag_start_next_trial = 0;

// timers
unsigned long state_timer = -1;


//// Setup function
void setup()
{
  Serial.begin(115200);
  Serial.println((String) millis() + " DBG begin setup");
}


//// Loop function
void loop()
{ /* Called over and over again. On each call, the behavior is determined
     by the current state.
  */
  
  //// Variable declarations
  // get the current time as early as possible in this function
  unsigned long time = millis();
  
  // The next state, by default the same as the current state
  STATE_TYPE next_state = current_state;
  
  // other variables
  String received_chat;
  int status = 1;
  
  
  //// Perform actions that occur on every call, independent of state
  // Announce the time
  if (time >= speak_at)
  {
    Serial.println((String) time + " DBG");
    speak_at += interval;
  }

  // Receive and deal with chat
  received_chat = receive_chat();
  if (received_chat.length() > 0)
  {
    status = handle_chat(received_chat, trial_params, flag_start_next_trial);
    if (status != 0)
    {
      Serial.println((String) time + " DBG RC_ERR " + (String) status);
    }
  }
  
  //// Begin state-dependent operations
  switch (current_state)
  {
    //// TRIAL_START
    // This one should be the same for all protocols, although we need
    // to figure out how to not hard-code the parameter names.
    case TRIAL_START:
      // Set up the trial based on received trial parameters
      Serial.println((String) time + " TRL_START");
      Serial.println((String) time + " TRLP ITI " + trial_params.inter_trial_interval);
    
      next_state = INTER_TRIAL_INTERVAL;
      break;


    //// User defined states
    // This one is the canonical waiting state form.
    case INTER_TRIAL_INTERVAL:
      // Wait the specified amount of time
      if (state_timer == -1)
      {
        state_timer = time + trial_params.inter_trial_interval;
      }
      if (time > state_timer)
      {
        next_state = WAIT_FOR_NEXT_TRIAL;
        state_timer = -1;
      }
      break;
    
    
    //// WAIT_FOR_NEXT_TRIAL
    // This one should be the same for all protocols.
    case WAIT_FOR_NEXT_TRIAL:
      // Wait until we receive permission to continue  
      if (flag_start_next_trial)
      {
        // Announce that we have ended the trial and reset the flag
        Serial.println((String) time + " TRL_RELEASED");
        flag_start_next_trial = 0;
        
        // Proceed to next trial
        next_state = TRIAL_START;
      }
      
      break;
  }
  
  
  //// Update the state variable
  if (next_state != current_state)
  {
    Serial.println((String) time + " ST_CHG " + current_state + " " + next_state);
  }
  current_state = next_state;
  
  return;
}


