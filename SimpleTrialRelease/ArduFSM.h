/* Standard states and functions used by all ArduFSM protocols.

This header file defines the State class, from which all other State objects
derive. One of these is TimedState, which is a base class for states with a
specified duration.

It also defines the "standard states": StateWaitToStartTrial,
StateTrialStart, and StateFinishTrial. These are instantiated in
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

//// Basic State definition
// Every State defines a run method, which returns a pointer to the next State.
class State
{
  public:
    State() { };
    virtual State* run(unsigned long time);
    int id = 0;
};


//// Derived TimedState with a duration
// This provides a unified "run" syntax to handle the duration
// Derived classes may implement s_setup, loop, s_finish, and update
// Briefly, on the first "run", the timer is set to be the current time
// plus the duration and s_setup() is run. Then, and on subsequent runs,
// loop() is called, unless the timer has elapsed or flag_stop has been set,
// in which case s_finish() is run.
// The state can be changed by s_finish(), or even by loop(). The latter would
// be useful for transitioning to another state while keeping the timer going.
class TimedState : public State
{
  protected:
    // flags and timers
    unsigned long time_of_last_call = 0;
    unsigned long timer = 0;
    unsigned long duration = 0;
    bool flag_stop = 0;
  
    // virtual functions, to be determined by the derived class
    virtual void s_setup() {};
    virtual State* loop() {};
    virtual State* s_finish() {};
  
  public:
    TimedState(long d) : duration(d) { 
      // All param_values are "long", so we take a long here, even though
      // a negative duration wouldn't make any sense.
      if (d < 0) Serial.println("ERR duration <0"); 
    };
    
    // the main run function
    State* run(unsigned long time);
    
    // setter for duration
    void set_duration(unsigned long new_duration);
    
    // generic setters, to be determined by the derived class
    virtual void update() {};
};


//// Definitions of standard states
// This one waits to receive the start trial signal
class StateWaitToStartTrial : public State {
  protected:
    State* run(unsigned long time);
  public:
    StateWaitToStartTrial() : State() { };
    int id = 1;
};

// This one runs once when the trial starts
class StateTrialStart : public State {
  protected:
    State* run(unsigned long time);
  public:
    StateTrialStart() : State() { };
    int id = 2;
};

// This one runs at the end of each trial
class StateFinishTrial : public TimedState {
  protected:
    void s_setup();
    State* s_finish();
  public:
    StateFinishTrial(long d) : TimedState(d) { };
    int id = 3;
};


//// State variable hooks
// These state variables are instantiated in ArduFSM.cpp, and we want to
// provide hooks to them, so that user-written states can return pointers
// to them.
extern State* state_wait_to_start_trial;
extern State* state_trial_start;
extern State* state_finish_trial;


//// Definitions of standard functions
// We provide a skeleton setup() with hooks to protocol-specific functions
void setup();

// Utility function to announce state changes at end of each loop
void announce_state_change(unsigned long time, State *curent_state,
  State *next_state);


#endif