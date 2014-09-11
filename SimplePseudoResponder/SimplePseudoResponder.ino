/* Simple protocol to test the setting of trial-by-trial settings.

Waits to receive a rewarded side, and maybe some other stuff.
Randomly generates a response.

TODO
----
* Move the required states, like TRIAL_START and WAIT_FOR_NEXT_TRIAL,
  into chat.cpp.
* Some standard way to create waiting states.
* Think about fixing the variables at the beginning of each trial.
* Wait to receive params for first trial before starting
* move definitions of trial_params to header file, so can be auto-generated

Here are the things that the user should have to change for each protocol:
* Enum of states
* User-defined states in switch statement
* param_abbrevs, param_values, tpidx_*, N_TRIAL_PARAMS

*/
#include "chat.h"


//// States
// Defines the finite state machine for this protocol
enum STATE_TYPE
{
  TRIAL_START,
  RESPONSE_WINDOW,
  INTER_TRIAL_INTERVAL,
  WAIT_FOR_NEXT_TRIAL
} current_state = TRIAL_START;


//// Global trial parameters structure. This holds the current value of
// all parameters. Should probably also make a copy to hold the latched
// values on each trial.
// Characteristics of each trial. These can all be modified by the user.
// However, there is no guarantee that the newest value will be used until
// the current trial is released.
#define N_TRIAL_PARAMS 5
#define tpidx_STPPOS 0
#define tpidx_MRT 1
#define tpidx_RWSD 2
#define tpidx_SRVPOS 3
#define tpidx_ITI 4
String param_abbrevs[N_TRIAL_PARAMS] = {"STPPOS", "MRT", "RWSD", "SRVPOS", "ITI"};
unsigned long param_values[N_TRIAL_PARAMS] = {0, 1, 1, 0, 3000};

//// Global trial results structure. Can be set by user-defined states. 
// Will be reported during mandatory INTER_TRIAL_INTERVAL state.
#define N_TRIAL_RESULTS 1
#define tridx_RESPONSE 0
String results_abbrevs[N_TRIAL_RESULTS] = {"RESPONSE"};
unsigned long results_values[N_TRIAL_RESULTS] = {0};
unsigned long default_results_values[N_TRIAL_RESULTS] = {0};


//// Miscellaneous globals
// Debugging announcements
unsigned long speak_at = 1000;
unsigned long interval = 1000;

// flag to remember whether we've received the start next trial signal
bool flag_start_next_trial = 0;

// timers
unsigned long state_timer = -1;

//// Declarations
int take_action(String protocol_cmd, String argument1);

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
  String protocol_cmd = (String) "";
  String argument1 = (String) "";
  String argument2 = (String) "";
  int status = 1;
  
  
  //// Perform actions that occur on every call, independent of state
  // Announce the time
  if (time >= speak_at)
  {
    Serial.println((String) time + " DBG");
    speak_at += interval;
  }

  //// Receive and deal with chat
  received_chat = receive_chat();
  if (received_chat.length() > 0)
  {
    // Attempt to parse
    status = handle_chat(received_chat, flag_start_next_trial,
        protocol_cmd, argument1, argument2);
    if (status != 0)
    {
      // Parse/syntax error
      Serial.println((String) time + " DBG RC_ERR " + (String) status);
    }
    else if (protocol_cmd.length() > 0)
    {
      // Protocol action required
      status = take_action(protocol_cmd, argument1, argument2);
      
      if (status != 0)
      {
        // Parse/syntax error
        Serial.println((String) time + " DBG TA_ERR " + (String) status);
      }
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
      for(int i=0; i < N_TRIAL_PARAMS; i++)
      {
        Serial.println((String) time + " TRLP " + (String) param_abbrevs[i] + 
          " " + (String) param_values[i]);
      }
    
      // Set up trial_results to defaults
      for(int i=0; i < N_TRIAL_RESULTS; i++)
      {
        results_values[i] = default_results_values[i];
      }      
    
      next_state = RESPONSE_WINDOW;
      break;

    //// User defined states
    case RESPONSE_WINDOW:
      // Randomly choose a response
      results_values[tridx_RESPONSE] = random(0, 2) + 1;
      
      next_state = INTER_TRIAL_INTERVAL;
      break;

    //// INTER_TRIAL_INTERVAL
    // Example of canonical waiting state.
    // Also announced trial_results.
    case INTER_TRIAL_INTERVAL:
      // Wait the specified amount of time
      if (state_timer == -1)
      {
        // Start timer and run first-time code
        state_timer = time + param_values[tpidx_ITI];

        // First-time code: Report results
        for(int i=0; i < N_TRIAL_RESULTS; i++)
        {
          Serial.println((String) time + " TRLR " + (String) results_abbrevs[i] + 
            " " + (String) results_values[i]);
        }
      }
      if (time > state_timer)
      {
        // Check timer and run every-time code
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


//// Take protocol action based on user command (ie, setting variable)
int take_action(String protocol_cmd, String argument1, String argument2)
{ /* Protocol action.
  
  Currently the only possible action is setting a parameter. In this case,
  protocol_cmd must be "SET". argument1 is the variable name. argument2 is
  the data.
  
  This logic could be incorporated in TrialSpeak, but we would need to provide
  the abbreviation, full name, datatype, and optional handling logic for
  each possible variable. So it seems to make more sense here.
  
  Return values:
  0 - command parsed successfully
  2 - unimplemented protocol_cmd
  4 - unknown variable on SET command
  5 - data conversion error
  */
  int status;
  
  if (protocol_cmd == "SET")
  {
    // Find index into param_abbrevs
    int idx = -1;
    for (int i=0; i < N_TRIAL_PARAMS; i++)
    {
      if (param_abbrevs[i] == argument1)
      {
        idx = i;
        break;
      }
    }
    
    // Error if not found, otherwise set
    if (idx == -1)
    {
      return 4;
    }
    else
    {
      // Convert to int
      status = safe_int_convert(argument2, param_values[idx]);
      if (status != 0)
      {
        return 5;
      }
    }
  }    
  else
  {
    // unknown command
    return 2;
  }
  
  return 0;
}


int safe_int_convert(String string_data, long unsigned int &variable)
{ /* Check that string_data can be converted to int before setting variable.
  
  Currently, variable cannot be set to 0 using this script. That is because
  toInt returns 0 upon error condition.
  
  Not sure how to handle the case when variable is some other kind of int?
  
  Returns 1 if string data converts to 0 (ie, an error occurs).
  */
  int conversion_var = string_data.toInt();
  if (conversion_var == 0)
  {
    return 1;
  }
  else 
  {
    variable = conversion_var;
  }  
  return 0;
}