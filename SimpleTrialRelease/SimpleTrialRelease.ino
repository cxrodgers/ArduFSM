/* Simple protocol to test the "trial release" functionality. 

On each trial, the arduino does nothing except listen for chats and
waits to receive a "RELEASE_TRL" command. Upon this command, it terminates
the current trial and begins the next one.
*/
#include "chat.h"


//// States
// Defines the finite state machine for this protocol
enum STATE_TYPE
{
  TRIAL_START,
  WAIT_FOR_NEXT_TRIAL
} current_state = TRIAL_START;


//// Miscellaneous globals
// Debugging announcements
unsigned long speak_at = 1000;
unsigned long interval = 1000;

// flag to remember whether we've received the start next trial signal
bool flag_start_next_trial = 0;


//// Setup function
void setup()
{
  Serial.begin(115200);
  Serial.println("DBG begin setup");
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
  
  
  //// Perform actions that occur on every call, independent of state
  // Announce the time
  if (time >= speak_at)
  {
    Serial.println((String) "DBG time " + time);
    speak_at += interval;
  }

  // Receive and deal with chat
  received_chat = receive_chat();
  if (received_chat == String("RELEASE_TRL\n"))
  {
    flag_start_next_trial = 1;
  }

  
  //// Begin state-dependent operations
  switch (current_state)
  {
    case TRIAL_START:
      // Set up the trial based on received trial parameters
      next_state = WAIT_FOR_NEXT_TRIAL;
    
      break;
    
    case WAIT_FOR_NEXT_TRIAL:
      // Wait until we receive permission to continue  
      if (flag_start_next_trial)
      {
        // Announce that we have ended the trial and reset the flag
        Serial.println("TRL_RELEASED");
        flag_start_next_trial = 0;
        
        // Proceed to next trial
        next_state = TRIAL_START;
      }
      
      break;
  }
  
  
  //// Update the state variable
  if (next_state != current_state)
  {
    Serial.println((String) "ST_CHG " + current_state + " " + next_state);
  }
  current_state = next_state;
  
  return;
}