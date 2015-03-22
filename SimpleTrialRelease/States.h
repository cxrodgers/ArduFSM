// Define the protocol-specific states used in SimpleTrialRelease
//
// This simple protocol uses only a single state called StateWait that
// does nothing.
//
// 
// Boilerplate documentation for all protocols
// ---
// To add a new state:
// 1) Define a new class, StateDoSomething, that derives from State or TimedState.
// 2) Define a new macro, STATE_ID_DO_SOMETHING, with a unique integer label,
//    and make that the value of "id".
// 3) Instantiate a single copy of StateDoSomething in States.cpp
// 4) Put an "extern" hook to that copy in States.h, so that the ino file
//    can use it. I guess this is only necessary for states that will be
//    referenced by user_start_trial() or similar.

#ifndef SIMPLETRIALRELEASE_STATES_H_
#define SIMPLETRIALRELEASE_STATES_H_

#include "ArduFSM.h"
#include "Params.h"

//// Unique state id, beginning with 10 to avoid overlap with standard states
#define STATE_ID_WAIT 10

// A simple waiting state
class StateWait : public TimedState {
  protected:
    State* s_finish();
  public:
    StateWait(long d) : TimedState(d) { };
    int id = STATE_ID_WAIT;
};


//// State variable hooks
// These state variables are instantiated in States.cpp, and we want to
// provide hooks to them, so that the ino file can reference them.
extern State* state_wait;

#endif // SIMPLETRIALRELEASE_STATES_H_