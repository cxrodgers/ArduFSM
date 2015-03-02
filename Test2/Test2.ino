#include "Arduino.h"

class State {
  public:
    State* run(unsigned long time);
    int my_id = 0;
};


class StateTrialStart : public State {
  public:
    void run(unsigned long time);
};

void setup() {
  // don't use parens if no arguments provided
  StateTrialStart state_trial_start;
  State next_state;
  
  next_state = state_trial_start;
}


void loop() {
    
}