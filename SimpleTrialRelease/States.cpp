// Implementations of states used in SimpleTrialRelease
#include "States.h"
#include "Arduino.h"


//// StateWait
State* StateWait::s_finish() {
  results_values[tridx_RESPONSE] = 1;
  return state_wait2;   
}

State* StateWait2::s_finish() {
  results_values[tridx_RESPONSE] = 1;
  return state_wait3;   
}

State* StateWait3::s_finish() {
  results_values[tridx_RESPONSE] = 1;
  return state_wait4;   
}

State* StateWait4::s_finish() {
  results_values[tridx_RESPONSE] = 1;
  return state_finish_trial;   
}

//// Instantiate one of each state
State* state_wait = new StateWait(param_values[tpidx_ITI]);
State* state_wait2 = new StateWait2(100);
State* state_wait3 = new StateWait3(120);
State* state_wait4 = new StateWait4(180);