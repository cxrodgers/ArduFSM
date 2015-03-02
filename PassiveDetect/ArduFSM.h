/* Header file for standard ArduFSM function */


#ifndef __ARDUFSM_H_INCLUDED
#define __ARDUFSM_H_INCLUDED

#include "Arduino.h" 
#include "TimedState.h"

void setup();

void announce_state_change(unsigned long time, State *curent_state,
  State *next_state);

// Standard state functions
void state_function_wait_to_start_trial(unsigned long time);
void state_function_trial_start(unsigned long time);


class StateTrialStart : public State {

  public:
    StateTrialStart() : State() { };
    void run(unsigned long time);
};



#endif