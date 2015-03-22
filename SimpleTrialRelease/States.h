// Define the protocol-specific states used in SimpleTrialRelease
#ifndef SIMPLETRIALRELEASE_STATES_H_
#define SIMPLETRIALRELEASE_STATES_H_

#include "ArduFSM.h"
#include "Params.h"

// These variables are defined in the protocol-specific Params file
extern char* param_abbrevs[N_TRIAL_PARAMS];
extern long param_values[N_TRIAL_PARAMS];
extern bool param_report_ET[N_TRIAL_PARAMS];
extern char* results_abbrevs[N_TRIAL_RESULTS];
extern long results_values[N_TRIAL_RESULTS];
extern long default_results_values[N_TRIAL_RESULTS];

// A simple waiting state
class StateWait : public TimedState {
  protected:
    State* s_finish();
  public:
    StateWait(long d) : TimedState(d) { };
};


//// State variable hooks
// These state variables are instantiated in States.cpp, and we want to
// provide hooks to them, so that the ino file can reference them.
extern State* state_wait;

#endif // SIMPLETRIALRELEASE_STATES_H_