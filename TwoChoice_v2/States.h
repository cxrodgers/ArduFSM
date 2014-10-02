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
// Attempt to have 0 be the "error value" since it cannot intentially be set to 0.
#define N_TRIAL_PARAMS 19
#define tpidx_STPPOS 0
#define tpidx_MRT 1
#define tpidx_REWSIDE 2
#define tpidx_SRVPOS 3
#define tpidx_ITI 4
#define tpidx_2PSTP 5
#define tpidx_SRV_FAR 6
#define tpidx_SRV_TRAVEL_TIME 7
#define tpidx_RESP_WIN_DUR 8
#define tpidx_INTER_REWARD_INTERVAL 9
#define tpidx_REWARD_DUR_L 10
#define tpidx_REWARD_DUR_R 11
#define tpidx_SERVO_SETUP_T 12
#define tpidx_PRE_SERVO_WAIT 13
#define tpidx_TERMINATE_ON_ERR 14
#define tpidx_ERROR_TIMEOUT 15
#define tpidx_STEP_SPEED 16
#define tpidx_STEP_FIRST_ROTATION 17
#define tpidx_STEP_INITIAL_POS 18


  


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
  SERVO_WAIT
};

// Declare
void rotate_motor(int rotation, unsigned int delay_ms=100);
int state_inter_rotation_pause(unsigned long time, long state_duration,
    STATE_TYPE& next_state);
int state_rotate_stepper1(STATE_TYPE& next_state);
int state_rotate_stepper2(STATE_TYPE& next_state);
int state_wait_for_servo_move(unsigned long time, unsigned long timer,
    STATE_TYPE& next_state);
int rotate(long n_steps);
  

class StateResponseWindow : public TimedState {
  protected:
    uint16_t my_touched = 0;
    unsigned int my_rewards_this_trial = 0;
    void loop();
    void s_finish();
    virtual void set_licking_variables(bool &, bool &);
  
  public:
    void update(uint16_t touched, unsigned int rewards_this_trial);
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

#endif