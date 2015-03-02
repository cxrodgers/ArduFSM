/* Header file for declaring protocol-specific states.
This implements a passive detection task.

Defines the following
* tpidx_ macros ... these allow you to index into trial_params
* tridx_ macros ... same, but for trial results
* the STATE_TYPE enum, which defines all possible states
* declarations for state functions and state objects, especially those derived
  from TimedState.

To define a new state, you should declare it here and put its implementation
into States.cpp.
*/


#ifndef __STATES_H_INCLUDED__
#define __STATES_H_INCLUDED__

#include "TimedState.h"


//// States
// Defines the finite state machine for this protocol
enum STATE_TYPE
{
  WAIT_TO_START_TRIAL,
  TRIAL_START,
  MOVE_STEPPER1,
  RESPONSE_WINDOW,
  REWARD_L,
  POST_REWARD_PAUSE,
  INTER_TRIAL_INTERVAL
};

// Declare utility functions
int rotate(long n_steps);

// Declare non-class states
int state_move_stepper1(STATE_TYPE& next_state);
  

//// Declare states that are objects
// Presently these all derive from TimedState
// Ensure that they have a public constructor, and optionally, a public
// "update" function that allows resetting of their parameters.
//
// Under protected, declare their protected variables, and declare any of
// s_setup, loop(), and s_finish() that you are going to define.


class StateRotateStepper1 : public State {

  public:
    StateRotateStepper1(): State() { };
    State* run(unsigned long time);
    int id = 3;
};


/* State functions */
//~ void state_function_wait_to_start_trial(unsigned long time, 
  //~ bool flag_start_trial);
//~ void state_function_trial_start(unsigned long time);
//~ void state_function_response_window(unsigned long time, uint16_t touched);
//~ void state_function_reward_l(unsigned long time);
//~ void state_function_inter_trial_interval(unsigned long time);

#endif