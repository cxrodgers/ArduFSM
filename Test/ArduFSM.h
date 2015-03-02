/* Header file for standard ArduFSM function */


#ifndef __ARDUFSM_H_INCLUDED
#define __ARDUFSM_H_INCLUDED

#include "Arduino.h" 
#include "TimedState.h"

void setup();



class StateTrialStart : public State {

  public:
    StateTrialStart() : State() { };
    State* run(unsigned long time);
    int id = 1;
};


class StateWaitToStartTrial : public State {

  public:
    StateWaitToStartTrial(): State() { };
    State* run(unsigned long time);
    int id = 2;
};

class StateInterTrialInterval : public TimedState {
  protected:
    void s_setup();
    State* s_finish();
  
  public:
    StateInterTrialInterval(unsigned long d) : TimedState(d) { };
};

void announce_state_change(unsigned long time, State *curent_state,
  State *next_state);


#endif