/* Implementation of the standard ArduFSM objects. */

#include "ArduFSM.h"
#include "Arduino.h"
#include "chat.h"

// These functions are defined in the protocol-specific *.ino file
extern void user_setup1();
extern void user_setup2();
extern void user_every_loop(unsigned long time);
extern State* user_trial_start(unsigned long time);

// Global so that we know whether the trial has started
// Needed by chat
bool flag_start_trial = 0;


//// Getter methods for the stuff in Params.h
extern long* get_param_values();
extern long* get_results_values();
extern char** get_results_abbrevs();
extern char** get_param_abbrevs();
extern int get_n_trial_params();
extern int get_n_trial_results();
extern bool* get_param_report_ET();
extern long* get_default_results_values();


// Instantiate the standard states
State* state_wait_to_start_trial = new StateWaitToStartTrial;
State* state_trial_start = new StateTrialStart;
State* state_finish_trial = new StateFinishTrial(
  1000);


//// Implementation of derived TimedState
State* TimedState::run(unsigned long time)
{ /* Boilerplate 'run' code for a state with a certain length of time.
    
  This is called on every pass, as long as the FSM is in this state.
  Depending on the current state of the timer, flag_stop, and the time, this
  calls s_setup(), loop(), or s_finish().

  States that inherit from this should define their own s_setup(), loop(),
  and s_finish().
    
  Simple algorithm:
    * If the timer is set to 0, take this to mean that we haven't started yet.
      Run s_setup()
      Set the timer and the flag
    * If the time is greater than the timer, or the flag_stop has been set,
      run the s_finish()
    * Otherwise, run loop()
  */
  // always store time of last call
  State* next_state;
  time_of_last_call = time;    
    
  // boiler plate timer code
  if (timer == 0)  {
    s_setup();
    flag_stop = 0;
    timer = time + duration;
  }
  
  if (flag_stop || (time >= timer))  {
    next_state = s_finish();
    timer = 0;      
  }
  else {
    next_state = loop();
  }
  
  return next_state;
};

void TimedState::set_duration(unsigned long new_duration) {
  /* Update the duration of the state, for instance after param change */
  duration = new_duration;
}


//// Implementations of standard states
// StateWaitToStartTrial
// Checks the global flag_start_trial, which is set by communications
// on every loop. Once the flag is true, issues the TRL_RELEASED token
// and resets the flag and continues to state_trial_start
State* StateWaitToStartTrial::run(unsigned long time)
{
  // Wait until we receive permission to continue  
  if (flag_start_trial) {
    // Announce that we have ended the trial and reset the flag
    Serial.print(time);
    Serial.println(" TRL_RELEASED");
    flag_start_trial = 0;
    return state_trial_start; // Proceed to next trial
  }
  return state_wait_to_start_trial;
}

// StateTrialStart
// Announces parameters
// Sets results to default values
// Calls user_trial_start
State* StateTrialStart::run(unsigned long time)
{ 
  // Get the values from Params.h
  long* param_values = get_param_values();
  long* results_values = get_results_values();
  int N_TRIAL_PARAMS = get_n_trial_params();
  int N_TRIAL_RESULTS = get_n_trial_results();
  char** param_abbrevs = get_param_abbrevs();
  char** results_abbrevs = get_results_abbrevs();
  bool* param_report_ET = get_param_report_ET();
  long* default_results_values = get_default_results_values();  
  
  // Set up the trial based on received trial parameters
  Serial.print(time);
  Serial.println(" TRL_START");
  for(int i=0; i < N_TRIAL_PARAMS; i++) {
    if (param_report_ET[i]) {
      // Buffered write would be nice here
      Serial.print(time);
      Serial.print(" TRLP ");
      Serial.print(param_abbrevs[i]);
      Serial.print(" ");
      Serial.println(param_values[i]);
    }
  }

  // Set up trial_results to defaults
  for(int i=0; i < N_TRIAL_RESULTS; i++) {
    results_values[i] = default_results_values[i];
  }      
  
  // Run user-specific trial start code, including setting next state
  return user_trial_start(time);
}


//// StateFinishTrial methods
// Announces results on setup
void StateFinishTrial::s_setup() {
  // Get the values from Params.h
  long* results_values = get_results_values();
  int N_TRIAL_RESULTS = get_n_trial_results();
  char** results_abbrevs = get_results_abbrevs();
  
  // Announce results
  for(int i=0; i < N_TRIAL_RESULTS; i++) {
    Serial.print(time_of_last_call);
    Serial.print(" TRLR ");
    Serial.print(results_abbrevs[i]);
    Serial.print(" ");
    Serial.println(results_values[i]);
  }
}

// Once the timer has elapsed, start the next trial.
State* StateFinishTrial::s_finish() {
  return state_wait_to_start_trial;   
}


//// Setup function
void setup()
{ /* Standard setup function to initialize the arduino.
  
  1. Initializes the serial port and announces time and (TODO) version info
  2. Runs a protocol-specific user_setup1() function that sets things like
     inputs/outpus before receiving any serial communcation.
  3. Runs serial communication until enough info has been received to run
     the first trial.
  4. Runs a protocol-specific user_setup2() function that finalizes anything
     that depens on receiving input, like 2-pin vs 4-pin mode.
  */
  unsigned long time = millis();
  int status = 1;
  
  // Initalize serial port communication and announce time
  Serial.begin(115200);
  Serial.print(time);
  Serial.println(" DBG begin setup");

  // Protocol-specific setup1, to be run before receiving any serial data
  user_setup1();

  // Run communications until we've received enough startup info to
  // start the first trial.
  while (!flag_start_trial)
  {
    status = communications(time);
    if (status != 0)
    {
      Serial.println("comm error in setup");
      delay(1000);
    }
  }
  
  // Now finalize the setup using the received initial parameters
  user_setup2();
}


//// Loop function
void loop()
{
  // All serial communications are marked with this time, so get it right
  // at the beginning
  unsigned long time = millis();
  
  // Current state variable, persistent across loops
  // The first time through, we want to initialize to wait_to_start_trial
  static State* current_state = state_wait_to_start_trial;
  static State* next_state = state_wait_to_start_trial;
  
  // misc
  int status = 1;
  
  // Run communications
  status = communications(time);
  
  // User-defined every-loop code
  user_every_loop(time);
  
  // State
  next_state = current_state->run(time);
  
  //// Update the state variable
  if (next_state != current_state)
  {
    announce_state_change(time, current_state, next_state);
  }
  current_state = next_state;
  
  return;
}


//// Utility functions
// Announce each state change
// We print the time at the beginning of the loop call, the current and
// next states, and the current time ("ST_CHG2"). The reason that we print
// the time at the beginning and end of the loop call is to help estimate
// the duration of certain states that take a long time (due to delay
// statements).
void announce_state_change(unsigned long time, State *current_state,
  State *next_state)
{
  Serial.print(time);
  Serial.print(" ST_CHG ");
  Serial.print(current_state->id());
  Serial.print(" ");
  Serial.println(next_state->id());

  Serial.print(millis());
  Serial.print(" ST_CHG2 ");
  Serial.print(current_state->id());
  Serial.print(" ");
  Serial.println(next_state->id());
}

