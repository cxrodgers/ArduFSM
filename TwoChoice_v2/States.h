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
#include <Servo.h>

//// Global trial parameters structure. This holds the current value of
// all parameters. Should probably also make a copy to hold the latched
// values on each trial.
// Characteristics of each trial. These can all be modified by the user.
// However, there is no guarantee that the newest value will be used until
// the current trial is released.
// Various types:
// * Should be latched, must be set at beginning ("RD_L")
// * Should be latched, can use default here ("SRVFAR")
// * Need to be set on every trial, else error ("STPPOS")
// * Some, like STPSPD, are not being updated
//
// * Init-only: those, like STPSPD, that are only used at the very beginning
// * Init-usually: those, like SRV_FAR, that could be varied later, but
//   the use case is infrequent (or never) and possibly untested.
// * Trial-required: those, like rewside, that must be specified on each trial 
//   or error.
// * Latched: those, like TO, that will often vary within a session
//
// Reported on each trial: trial-required, maybe latched
// Reported initially only: init-only, probably init-usually
// Reported on change only: latched, maybe init-usually
//
// Decision 1: Report latched on each trial or only on change?
// Decision 2: Should init-usually be treated more like latched (see above),
//             or more like init-only?
//
// The main things to add to this code are:
// * Report TRLP only those that are marked "report-on-each-trial"
// * Do not release trial until all "required-on-each-trial" are set
// And we can argue about how these two categories map onto the categories above.
//
// Attempt to have 0 be the "error value" since it cannot intentially be set to 0.
#define N_TRIAL_PARAMS 24
#define tpidx_STPPOS 0 // reqd
#define tpidx_MRT 1 // latch
#define tpidx_REWSIDE 2 // reqd
#define tpidx_SRVPOS 3 //reqd
#define tpidx_ITI 4 // init-usually
#define tpidx_2PSTP 5 // init-only
#define tpidx_SRV_FAR 6 // init-usually
#define tpidx_SRV_TRAVEL_TIME 7 // init-usually
#define tpidx_RESP_WIN_DUR 8 // init-usually
#define tpidx_INTER_REWARD_INTERVAL 9 // init-usually
#define tpidx_REWARD_DUR_L 10 // init-usually
#define tpidx_REWARD_DUR_R 11 // init-usually
#define tpidx_SERVO_SETUP_T 12 // init-only
#define tpidx_PRE_SERVO_WAIT 13 // init-usually
#define tpidx_TERMINATE_ON_ERR 14 // latched
#define tpidx_ERROR_TIMEOUT 15 // latched
#define tpidx_STEP_SPEED 16 // init-only
#define tpidx_STEP_FIRST_ROTATION 17 // init-usually
#define tpidx_STEP_INITIAL_POS 18 // init-only
#define tpidx_IS_RANDOM 19 // reqd
#define tpidx_TOU_THRESH 20 // init-only
#define tpidx_REL_THRESH 21 // init-only
#define tpidx_STP_HALL 22
#define tpidx_STP_POSITIVE_STPPOS 23 

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
  ROTATE_STEPPER1,
  INTER_ROTATION_PAUSE,
  ROTATE_STEPPER2,
  MOVE_SERVO,
  WAIT_FOR_SERVO_MOVE,
  RESPONSE_WINDOW,
  REWARD_L,
  REWARD_R,
  POST_REWARD_TIMER_START,
  POST_REWARD_TIMER_WAIT,
  START_INTER_TRIAL_INTERVAL,
  INTER_TRIAL_INTERVAL,
  ERROR,
  PRE_SERVO_WAIT,
  SERVO_WAIT,
  POST_REWARD_PAUSE,
};

// Declare utility functions
int rotate(long n_steps);
int rotate_to_sensor(int step_size, bool positive_peak, long set_position);

// Declare non-class states
int state_inter_rotation_pause(unsigned long time, long state_duration,
    STATE_TYPE& next_state);
int state_rotate_stepper1(STATE_TYPE& next_state);
int state_rotate_stepper2(STATE_TYPE& next_state);
int state_wait_for_servo_move(unsigned long time, unsigned long timer,
    STATE_TYPE& next_state);
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


class StateFakeResponseWindow : public StateResponseWindow {
  /* A version of StateResponseWindow that randomly makes decisions */
  protected:
    void set_licking_variables(bool &, bool &);
  
  public:
    StateFakeResponseWindow(unsigned long d) : StateResponseWindow(d) { };
};


class StateInterRotationPause : public TimedState {
  protected:
    void s_finish();
  
  public:
    StateInterRotationPause(unsigned long d) : TimedState(d) { };
};

class StateErrorTimeout : public TimedState {
  protected:
    Servo my_linServo;
  
    void s_setup();
    void s_finish();
  
  public:
    StateErrorTimeout(unsigned long d, Servo linServo) : TimedState(d) {
      my_linServo = linServo;
    };
};

class StateWaitForServoMove : public TimedState {
  protected:
    Servo my_linServo;
    void s_setup();
    void s_finish();
  
  public:
    void update(Servo linServo);
    StateWaitForServoMove(unsigned long d) : TimedState(d) { };
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