/* Passive detection task.
*/
#include "chat.h"
#include "hwconstants.h"
#include "mpr121.h"
#include <Wire.h> // also for mpr121
#include <Stepper.h>
#include "TimedState.h"
#include "States.h"
#include "Params.h"
#include "Actions.h"
#include "ArduFSM.h"

//// Standard globals
// flag to remember whether we've received the start next trial signal
bool flag_start_trial = 0;

// params and results
extern char* param_abbrevs[N_TRIAL_PARAMS];
extern long param_values[N_TRIAL_PARAMS];
extern bool param_report_ET[N_TRIAL_PARAMS];
extern char* results_abbrevs[N_TRIAL_RESULTS];
extern long results_values[N_TRIAL_RESULTS];
extern long default_results_values[N_TRIAL_RESULTS];

// state monitor
extern State* current_state;

Stepper *stimStepper = 0;

void user_setup1() { }
void user_setup2() { }
void user_every_loop() { }


//// Loop function
void loop()
{ /* Called over and over again. On each call, the behavior is determined
     by the current state.
  */
  
  //// Variable declarations
  // get the current time as early as possible in this function
  unsigned long time = millis();

  // The next state, by default the same as the current state
  State *next_state = current_state;

  // misc
  int status = 1;
  
  //// Run communications
  status = communications(time);
  
  //// User protocol code
  user_every_loop();

  //// Begin state-dependent operations
  // The relevant state function or object is called for the current state.
  // next_state will be set
  // TODO: have it return next_state instead of setting
  // TODO: make each state an object so we can just do next_state.run(time)
  next_state = current_state->run(time);


  //// Update the state variable
  if (next_state != current_state)
  {
    //announce_state_change(time, current_state, next_state);
  }
  current_state = next_state;
  
  return;
}

