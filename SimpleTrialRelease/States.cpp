#include "States.h"
#include "Arduino.h"

//// StateWait
State* StateWait::s_finish() {
  return state_finish_trial;   
}


//// Instantiate the states
State* state_wait = new StateWait(param_values[tpidx_ITI]);