// Define the protocol-specific states used in TwoChoice
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


#ifndef __STATES_H_INCLUDED__
#define __STATES_H_INCLUDED__

#include <Servo.h>
#include "ArduFSM.h"


//// Unique state id, beginning with 10 to avoid overlap with standard states
#define STATE_ROTATE_STEPPER1             10
#define STATE_INTER_ROTATION_PAUSE        11
#define STATE_ROTATE_STEPPER2             12 
#define STATE_MOVE_SERVO                  13
#define STATE_WAIT_FOR_SERVO_MOVE         14
#define STATE_RESPONSE_WINDOW             15
#define STATE_REWARD_L                    16
#define STATE_REWARD_R                    17
#define STATE_POST_REWARD_TIMER_START     18
#define STATE_POST_REWARD_TIMER_WAIT      19
#define STATE_ERROR_TIMEOUT               22
#define STATE_PRE_SERVO_WAIT              23
#define STATE_SERVO_WAIT                  24
#define STATE_POST_REWARD_PAUSE           25
 

//// Hooks to state variables instantiated in States.cpp.
// These allow three things:
// 1) To refer to them below in order to define state transitions
// 2) To refer to them in other files that include this one. For instance,
//    in the ino file, we will use one of the below to define the first state.
// 3) To use them in the implementations of each state before they have been
//    instantiated.
extern State* state_rotate_stepper1;
extern State* state_rotate_stepper2;
extern State* state_response_window;
extern State* state_reward_l;
extern State* state_reward_r;
extern State* state_error_timeout;
extern State* state_inter_rotation_pause;
extern State* state_wait_for_servo_move;
extern State* state_post_reward_pause;

// Declare utility functions
int rotate(long n_steps);
int rotate_to_sensor(int step_size, bool positive_peak, long set_position);


//// Define derived State objects
// StateRotateStepper1 : Rotate the stepper motor in the direction defined 
// by step_first_rotation and transition to inter_rotation_pause.
class StateRotateStepper1 : public State {
  public:
    State* run(unsigned long time);
    int id() { return STATE_ROTATE_STEPPER1; }
};

// StateRotateStepper2 : calculate how much rotation is needed to reach
// final position and do it.
class StateRotateStepper2 : public State {
  public:
    State* run(unsigned long time);
    int id() { return STATE_ROTATE_STEPPER2; }
};

// StateRewardL : deliver reward to left pipe
class StateRewardL : public State {
  public:
    State* run(unsigned long time);
    int id() { return STATE_REWARD_L; }
};

// StateRewardR : deliver reward to right pipe
class StateRewardR : public State {
  public:
    State* run(unsigned long time);
    int id() { return STATE_REWARD_R; }
};


//// Define derived TimedState objects
// StateResponseWindow : waits for response
class StateResponseWindow : public TimedState {
  protected:
    // Remember touched and rewards per trial  
    uint16_t my_touched = 0;
    unsigned int my_rewards_this_trial = 0;
    
    // Virtual loop and finish states
    State* loop();
    State* s_finish();
  
    // Virtual function to set licking, so that derived classes can override
    virtual void set_licking_variables(bool &, bool &);
  
  public:
    void update(uint16_t touched);
    StateResponseWindow(unsigned long d) : TimedState(d) { }
    int id() { return STATE_RESPONSE_WINDOW; }
};

// StateFakeResponseWindow : generates a fake response
class StateFakeResponseWindow : public StateResponseWindow {
  protected:
    void set_licking_variables(bool &, bool &);
  
  public:
    StateFakeResponseWindow(unsigned long d) : StateResponseWindow(d) { }
};

// StateInterRotationPause : waits between stepper rotations and
// transitions to state_rotate_stepper2 when done.
class StateInterRotationPause : public TimedState {
  protected:
    State* s_finish() { return state_rotate_stepper2; }
  
  public:
    StateInterRotationPause(unsigned long d) : TimedState(d) { }
    int id() { return STATE_INTER_ROTATION_PAUSE; }    
};

// StateErrorTimeout : waits for error timeout and transitions to
// state_inter_trial_interval when finished
class StateErrorTimeout : public TimedState {
  protected:
    void s_setup();
    State* s_finish() { return state_finish_trial; }
  
  public:
    StateErrorTimeout(unsigned long d) : TimedState(d) { };
    int id() { return STATE_ERROR_TIMEOUT; }        
};

// StateWaitForServoMove : wait specified amount of time for servo to finish,
// and then transitions to state_response_window.
class StateWaitForServoMove : public TimedState {
  protected:
    void s_setup();
    State* s_finish() { return state_response_window; }
  
  public:
    StateWaitForServoMove(unsigned long d) : TimedState(d) { };
    int id() { return STATE_WAIT_FOR_SERVO_MOVE; }
};

// StatePostRewardPause : wait in between rewards and transition back to
// state_response_window.
class StatePostRewardPause : public TimedState {
  protected:
    State* s_finish() { return state_response_window; }
  
  public:
    StatePostRewardPause(unsigned long d) : TimedState(d) { };
    int id() { return STATE_POST_REWARD_PAUSE; }
};


//// Accessor methods for static variables like motors
Servo* get_servo();


#endif // __STATES_H_INCLUDED__