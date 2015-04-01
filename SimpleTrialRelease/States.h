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
// 4) Put an "extern" hook to that copy in States.h.

#ifndef SIMPLETRIALRELEASE_STATES_H_
#define SIMPLETRIALRELEASE_STATES_H_

#include "ArduFSM.h"
#include "Params.h"

//// Unique state id, beginning with 10 to avoid overlap with standard states
#define STATE_ID_WAIT 10
#define STATE_ID_WAIT2 11
#define STATE_ID_WAIT3 12
#define STATE_ID_WAIT4 13


//// Hooks to state variables instantiated in States.cpp.
// These allow three things:
// 1) To refer to them below in order to define state transitions
// 2) To refer to them in other files that include this one. For instance,
//    in the ino file, we will use one of the below to define the first state.
// 3) To use them in the implementations of each state before they have been
//    instantiated.
extern State* state_wait;
extern State* state_wait2;
extern State* state_wait3;
extern State* state_wait4;


// A simple waiting state
class StateWait : public TimedState {
  protected:
    State* s_finish();
  public:
    StateWait(long d) : TimedState(d) { };
    int id() { return STATE_ID_WAIT; }    
};

// A simple waiting state
class StateWait2 : public TimedState {
  protected:
    State* s_finish();
  public:
    StateWait2(long d) : TimedState(d) { };
    int id() { return STATE_ID_WAIT2; }    
};

// A simple waiting state
class StateWait3 : public TimedState {
  protected:
    State* s_finish();
  public:
    StateWait3(long d) : TimedState(d) { };
    int id() { return STATE_ID_WAIT3; }    
};

// A simple waiting state
class StateWait4 : public TimedState {
  protected:
    State* s_finish();
  public:
    StateWait4(long d) : TimedState(d) { };
    int id() { return STATE_ID_WAIT4; }    
};

#endif // SIMPLETRIALRELEASE_STATES_H_