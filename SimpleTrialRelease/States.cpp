// Implementations of states used in SimpleTrialRelease
#include "States.h"
#include "Arduino.h"


//// StateWait
State* StateWait::s_finish() {
  results_values[tridx_RESPONSE] = 1;
  return state_finish_trial;   
}


//// Instantiate one of each state
State* state_wait = new StateWait(param_values[tpidx_ITI]);