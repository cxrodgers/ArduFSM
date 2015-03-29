// Implementations of states used in TwoChoice
#include "States.h"
#include "mpr121.h"
#include "Arduino.h"
#include "hwconstants.h"
#include "Stepper.h"
#include "chat.h"
#include "Params.h"


//// Globals, defined in ino.
extern long sticky_stepper_position;
extern Stepper* stimStepper;


//// Accessor methods for static variables for hardware
Servo* get_servo() {
  static Servo *servo = new Servo;
  return servo;
}

// This function returns the current touched status. If repoll is True,
// it repolls and stores the updated version. Otherwise it returns the
// cached version. We only repoll in user_every_loop so that we can announce
// it. During response_window, we just check the cached value.
uint16_t get_touch_status(bool repoll) {
  static uint16_t sticky_touched = 0;
  if (repoll)
    sticky_touched = pollTouchInputs();
  return sticky_touched;
}


//// StateResponseWindow implementation
// Determines whether a response has just occurred, and depending
// on trial contingencies, will set results_values and tranisition
// to state_reward_l, state_reward_r, state_error_timeout. If no
// response given, will stay in the same state.
State* StateResponseWindow::loop() {
  int current_response;
  bool licking_l;
  bool licking_r;
  State* next_state = this;
  
  // get the licking state 
  // overridden in FakeResponseWindow
  set_licking_variables(licking_l, licking_r);
  
  // transition if max rewards reached
  if (my_rewards_this_trial >= param_values[tpidx_MRT])
  {
    flag_stop = 1;
    return state_finish_trial;
  }

  // Do nothing if both or neither are being licked.
  // Otherwise, assign current_response.
  if (!licking_l && !licking_r)
    return this;
  else if (licking_l && licking_r)
    return this;
  else if (licking_l && !licking_r)
    current_response = __TRIAL_SPEAK_CHOICE_LEFT;
  else if (!licking_l && licking_r)
    current_response = __TRIAL_SPEAK_CHOICE_RIGHT;
  else
    Serial.println("ERR this should never happen");

  // Only assign result if this is the first response
  if (results_values[tridx_RESPONSE] == 0)
    results_values[tridx_RESPONSE] = current_response;
  
  // Move to reward state, or error if TOE is set, or otherwise stay
  if ((current_response == __TRIAL_SPEAK_CHOICE_LEFT) && (
      param_values[tpidx_REWSIDE] == __TRIAL_SPEAK_CHOICE_LEFT))
  { // Hit on left
    next_state = state_reward_l;
    my_rewards_this_trial++;
    results_values[tridx_OUTCOME] = __TRIAL_SPEAK_OUTCOME_HIT;
  }
  else if ((current_response == __TRIAL_SPEAK_CHOICE_RIGHT) && (
      param_values[tpidx_REWSIDE] == __TRIAL_SPEAK_CHOICE_RIGHT))
  { // Hit on right
    next_state = state_reward_r;
    my_rewards_this_trial++;
    results_values[tridx_OUTCOME] = __TRIAL_SPEAK_OUTCOME_HIT;
  }
  else if (param_values[tpidx_TERMINATE_ON_ERR] == __TRIAL_SPEAK_NO)
  { // Error made, TOE is false
    // Decide how to deal with this non-TOE case
  }
  else
  { // Error made, TOE is true
    next_state = state_error_timeout;
    results_values[tridx_OUTCOME] = __TRIAL_SPEAK_OUTCOME_ERROR;
  }
    
  return next_state;
}

// The timer is up, so set results values to spoil if nothing has happened
// yet, and transition to state_inter_trial_interval.
State* StateResponseWindow::s_finish()
{
  // If response is still not set, mark as spoiled
  if (results_values[tridx_RESPONSE] == 0)
  {
    results_values[tridx_RESPONSE] = __TRIAL_SPEAK_CHOICE_NOGO;
    results_values[tridx_OUTCOME] = __TRIAL_SPEAK_OUTCOME_SPOIL;
  }
  
  // Stuff that needs to happen at beginning of ITI
  digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, HIGH);
  get_servo()->write(param_values[tpidx_SRV_FAR]);
  return state_finish_trial;
}

// Gets the current licking status from the touched variable for each port
// We don't repoll, because otherwise we wouldn't be able to announce that
// event.
void StateResponseWindow::set_licking_variables(
  bool &licking_l, bool &licking_r) { 
  uint16_t my_touched = get_touch_status(0);
  licking_l = (get_touched_channel(my_touched, 0) == 1);
  licking_r = (get_touched_channel(my_touched, 1) == 1);    
}


//// StateFakeResponsewindow
// Differs only in that it randomly fakes a response by randomly choosing licks
void StateFakeResponseWindow::set_licking_variables(
  bool &licking_l, bool &licking_r) {
  uint16_t my_touched = get_touch_status(0);    
  licking_l = (random(0, 10000) < 3);    
  licking_r = (random(0, 10000) < 3);   
}


//// StateErrorTimeout
void StateErrorTimeout::s_setup() {
  digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, HIGH);
  get_servo()->write(param_values[tpidx_SRV_FAR]);
}


//// StateWaitForServoMove
void StateWaitForServoMove::s_setup() {
  get_servo()->write(param_values[tpidx_SRVPOS]);
}


//// StateRotateStepper1
State* StateRotateStepper1::run(unsigned long time) {
  //~ rotate(param_values[tpidx_STEP_FIRST_ROTATION]);
  return state_inter_rotation_pause;
}


//// StateRotateStepper2
State* StateRotateStepper2::run(unsigned long time) {

  return state_wait_for_servo_move;
}


//// The reward states use delay because they need to be millisecond-precise
State* StateRewardL::run(unsigned long time) {

  return state_post_reward_pause;
}

State* StateRewardR::run(unsigned long time) {


  return state_post_reward_pause;
}



//// Instantiate one of each state
State* state_rotate_stepper1 = new StateRotateStepper1();
State* state_rotate_stepper2 = new StateRotateStepper2();
State* state_reward_l = new StateRewardL();
State* state_reward_r = new StateRewardR();
State* state_response_window = new StateResponseWindow(
  param_values[tpidx_RESP_WIN_DUR]);
State* state_inter_rotation_pause = new StateInterRotationPause(50);
State* state_wait_for_servo_move = new StateWaitForServoMove(
  param_values[tpidx_SRV_TRAVEL_TIME]);
State* state_error_timeout = new StateErrorTimeout(
  param_values[tpidx_ERROR_TIMEOUT]);
State* state_post_reward_pause = new StatePostRewardPause(
  param_values[tpidx_INTER_REWARD_INTERVAL]);

