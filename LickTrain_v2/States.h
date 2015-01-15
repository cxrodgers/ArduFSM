/* Header file for declaring protocol-specific states.
This implements a two-alternative choice task with two lick ports.

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

//// Global trial parameters structure. This holds the current value of
// all parameters. Should probably also make a copy to hold the latched
// values on each trial.
// Characteristics of each trial. These can all be modified by the user.
// However, there is no guarantee that the newest value will be used until
// the current trial is released.
//
// Attempt to have 0 be the "error value" since it cannot intentially be set to 0.
#define N_TRIAL_PARAMS 8
#define tpidx_MRT 0 // latch
#define tpidx_REWSIDE 1 // reqd
#define tpidx_INTER_REWARD_INTERVAL 2 // init-usually
#define tpidx_REWARD_DUR_L 3 // init-usually
#define tpidx_REWARD_DUR_R 4 // init-usually
#define tpidx_TOU_THRESH 5 // init-only
#define tpidx_REL_THRESH 6 // init-only
#define tpidx_RESP_WIN_DUR 7


//// Global trial results structure. Can be set by user-defined states. 
// Will be reported during mandatory INTER_TRIAL_INTERVAL state.
#define N_TRIAL_RESULTS 2
#define tridx_RESPONSE 0
#define tridx_OUTCOME 1


//// Defines for commonly used things
// Move this to TrialSpeak, and rename CHOICE_LEFT etc
#define LEFT 1
#define RIGHT 2
#define NOGO 3

#define OUTCOME_HIT 1
#define OUTCOME_ERROR 2
#define OUTCOME_SPOIL 3

//// States
// Defines the finite state machine for this protocol
enum STATE_TYPE
{
  WAIT_TO_START_TRIAL,
  TRIAL_START,
  RESPONSE_WINDOW,
  REWARD_L,
  REWARD_R,
  POST_REWARD_PAUSE,
  INTER_TRIAL_INTERVAL,
};

// Declare non-class states
int state_reward_l(STATE_TYPE& next_state);
int state_reward_r(STATE_TYPE& next_state);


//// Declare states that are objects
// Presently these all derive from TimedState
// Ensure that they have a public constructor, and optionally, a public
// "update" function that allows resetting of their parameters.
//
// Under protected, declare their protected variables, and declare any of
// s_setup, loop(), and s_finish() that you are going to define.
class StateResponseWindow : public TimedState {
  protected:
    uint16_t my_touched = 0;
    unsigned int my_rewards_this_trial = 0;
    void loop();
    void s_finish();
    virtual void set_licking_variables(bool &, bool &);
  
  public:
    void update(uint16_t touched);
    StateResponseWindow(unsigned long d) : TimedState(d) { };
};

class StateInterTrialInterval : public TimedState {
  protected:
    void s_setup();
    void s_finish();
  
  public:
    StateInterTrialInterval(unsigned long d) : TimedState(d) { };
};

class StatePostRewardPause : public TimedState {
  protected:
    void s_finish();
  
  public:
    StatePostRewardPause(unsigned long d) : TimedState(d) { };
};

#endif