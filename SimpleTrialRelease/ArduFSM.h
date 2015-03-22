/* Standard states and functions used by all ArduFSM protocols.

This header file defines the State class, from which all other State objects
derive.

It also defines the "standard states": StateWaitToStartTrial,
StateTrialStart, and StateInterTrialInterval. These are instantiated in
ArduFSM.cpp.

Finally, it defines the setup() function, and other utility functions.

These standard functions call certain protocol-specific functions that
must be defined in the protocol *.ino file:
void user_setup1()
void user_setup2()
void user_every_loop()
State* user_trial_start()
*/
#ifndef __ARDUFSM_H_INCLUDED
#define __ARDUFSM_H_INCLUDED

#include "Arduino.h" 
#include "States.h"

//// Basic State definition
// Every State defines a run method, which returns a pointer to the next State.
class State
{
  public:
    State() { };
    virtual State* run(unsigned long time);
    int id = 0;
};


//// Definitions of standard states
// This one waits to receive the start trial signal
class StateWaitToStartTrial : public State {
  protected:
    State* run(unsigned long time);
  public:
    StateWaitToStartTrial() : State() { };
};

// This one runs once when the trial starts
class StateTrialStart : public State {
  protected:
    State* run(unsigned long time);
  public:
    StateTrialStart() : State() { };
};

// This one runs at the end of each trial
class StateInterTrialInterval : public State {
  protected:
    State* run(unsigned long time);
  public:
    StateInterTrialInterval() : State() { };
};


//// State variable hooks
// These state variables are instantiated in ArduFSM.cpp, and we want to
// provide hooks to them, so that user-written states can return pointers
// to them.
extern State* state_wait_to_start_trial;
extern State* state_trial_start;
extern State* state_inter_trial_interval;


//// Definitions of standard functions
// We provide a skeleton setup() with hooks to protocol-specific functions
void setup();

// Utility function to announce state changes at end of each loop
void announce_state_change(unsigned long time, State *curent_state,
  State *next_state);


#endif