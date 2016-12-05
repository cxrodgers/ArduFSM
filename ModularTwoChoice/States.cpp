/* Implementation file for declaring protocol-specific states.
This implements a two-alternative choice task with two lick ports.

Defines the following:
* param_abbrevs, which defines the shorthand for the trial parameters
* param_values, which define the defaults for those parameters
* results_abbrevs, results_values, default_results_values
* implements the state functions and state objects

*/

#include "States.h"
#include "Arduino.h"
#include "hwconstants.h"

#ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
#include "Stepper.h"
#endif

#ifndef __HWCONSTANTS_H_USE_IR_DETECTOR
#include "mpr121.h"
#endif

#ifdef __HWCONSTANTS_H_USE_IR_DETECTOR
#include "ir_detector.h"
#endif

#include <Servo.h>

// include this one just to get __TRIAL_SPEAK_YES
#include "chat.h"

//#define EXTRA_180DEG_ROT

extern STATE_TYPE next_state;

// These should go into some kind of Protocol.h or something
char* param_abbrevs[N_TRIAL_PARAMS] = {
  "STPPOS", "MRT", "RWSD", "SRVPOS", "ITI",
  "2PSTP", "SRVFAR", "SRVTT", "RWIN", "IRI",
  "RD_L", "RD_R", "SRVST", "PSW", "TOE",
  "TO", "STPSPD", "STPFR", "STPIP", "ISRND",
  "TOUT", "RELT", "STPHAL", "HALPOS", "DIRDEL",
  "OPTO",
  };
long param_values[N_TRIAL_PARAMS] = {
  1, 1, 1, 1, 3000,
  0, 1900, 4500, 45000, 500,
  40, 40, 1000, 1, 1,
  6000, 20, 50, 50, 0,
  6, 3, 0, 50, 0,
  0,
  };

// Whether to report on each trial  
// Currently, manually match this up with Python-side
// Later, maybe make this settable by Python, and default to all True
// Similarly, find out which are required on each trial, and error if they're
// not set. Currently all that are required_ET are also reported_ET.
bool param_report_ET[N_TRIAL_PARAMS] = {
  1, 0, 1, 1, 0,
  0, 0, 0, 0, 0,
  0, 0, 0, 0, 0,
  0, 0, 0, 0, 1,
  0, 0, 0, 0, 1,
  1,
};
  
char* results_abbrevs[N_TRIAL_RESULTS] = {"RESP", "OUTC"};
long results_values[N_TRIAL_RESULTS] = {0, 0};
long default_results_values[N_TRIAL_RESULTS] = {0, 0};

// Global, persistent variable to remember where the stepper is
long sticky_stepper_position = 0;


//// State definitions
#ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
extern Stepper* stimStepper;
#endif

extern Servo linServo;


// Make this true to generate random responses for debugging
#define FAKE_RESPONDER 0

// touched monitor
extern uint16_t sticky_touched;

extern uint16_t touched;

extern bool flag_start_trial;

  // statics 
  // these are just "declared" here, they can be modified at the beginning
  // of each trial
static StateWaitToStartTrial wait_to_start_trial;
static StateTrialStart start_trial;
static StateRotateStepper1 srs1;
static StateRotateStepper2 srs2;
static StateResponseWindow srw(param_values[tpidx_RESP_WIN_DUR]);
static StateFakeResponseWindow sfrw(param_values[tpidx_RESP_WIN_DUR]);
static StateInterRotationPause state_interrotation_pause(50);
static StateWaitForServoMove state_wait_for_servo_move(
  param_values[tpidx_SRV_TRAVEL_TIME]);
static StateInterTrialInterval state_inter_trial_interval(
  param_values[tpidx_ITI]);
static StateErrorTimeout state_error_timeout(
  param_values[tpidx_ERROR_TIMEOUT], linServo);
static StateRewardR reward_r;
static StateRewardL reward_l;
static StatePostRewardPause state_post_reward_pause(
      param_values[tpidx_INTER_REWARD_INTERVAL]);

//StateDependentOperations

void stateDependentOperations(STATE_TYPE current_state, unsigned long time) {
  switch(current_state) {
    //// Wait till the trial is released. Same for all protocols.
    case WAIT_TO_START_TRIAL:
      // Wait until we receive permission to continue  
      wait_to_start_trial.run();
      break;
    //// TRIAL_START. Same for all protocols.
    case TRIAL_START:
      start_trial.run();
      break;

     case MOVE_SERVO:
      // Start the servo moving and its timer
      // Should immediately go to ROTATE_STEPPER1, while th etimer is running.
      // After rotating, we'll wait for the timer to be completed.
      // This object is really more of a timer than a state.
      // OTOH, could argue that MOVE_SERVO and WAIT_FOR_SERVO_MOVE are 
      // the same state, and this distinction is just between the s_setup
      // and the rest of it.
      state_wait_for_servo_move.update(linServo);
      state_wait_for_servo_move.run(time);
      break;
    
    case ROTATE_STEPPER1:
      srs1.run();
      break;
    
    case INTER_ROTATION_PAUSE:
      state_interrotation_pause.run(time);
      break;
    
    case ROTATE_STEPPER2:
      srs2.run();
      break;

    case WAIT_FOR_SERVO_MOVE:
      // This state never actually happens, only MOVE_SERVO
      state_wait_for_servo_move.run(time);
      break;
    
    case RESPONSE_WINDOW:
      if (FAKE_RESPONDER)
      {
        sfrw.update(touched);
        sfrw.run(time);
      } 
      else 
      {
        srw.update(touched);
        srw.run(time);
      }
      break;
    
    case REWARD_L:
      reward_l.run(time);
      break;
    
    case REWARD_R:
      reward_r.run(time);
      break;
    
    case POST_REWARD_PAUSE:
      state_post_reward_pause.run(time);
      break;    
    
    case ERROR:
      // turn the light on
      digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, HIGH);
      
      state_error_timeout.run(time);
      break;

    case INTER_TRIAL_INTERVAL:
      // turn the light on
      digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, HIGH);

      // Move servo back
      linServo.write(param_values[tpidx_SRV_FAR]);

      // Announce trial_results
      state_inter_trial_interval.run(time);
      break;
 

  };
};





  

int rotate_to_sensor(int step_size, bool positive_peak, long set_position,
  int hall_sensor_id)
{ /* Rotate to a position where the Hall effect sensor detects a peak.
  
  step_size : typically 1 or -1, the number of steps to use between checks
  positive_peak : whether to stop when a positive or negative peak detected
  set_position : will set "sticky_stepper_position" to this afterwards
  hall_sensor_id : 1 or 2, depending on which hall sensor to read
  */
  bool keep_going = 1;
  int sensor;
  int prev_sensor = sensor;
  int actual_steps = 0;
  #ifdef __HWCONSTANTS_H_USE_STEPPER_DRIVER
  long nondirectional_steps = 0;
  #endif
  
  // Keep track of the previous values
  int sensor_history[__HWCONSTANTS_H_SENSOR_HISTORY_SZ] = {0};
  int sensor_history_idx = 0;
  
  if (hall_sensor_id == 1) {
    sensor = analogRead(__HWCONSTANTS_H_HALL1);
  } else if (hall_sensor_id == 2) {
    sensor = analogRead(__HWCONSTANTS_H_HALL2);
  }
  
  // Store in circular buffer
  sensor_history[sensor_history_idx] = sensor;
  sensor_history_idx = (sensor_history_idx + 1) % 
    __HWCONSTANTS_H_SENSOR_HISTORY_SZ;
  
  #ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
  digitalWrite(TWOPIN_ENABLE_STEPPER, HIGH);
  delay(__HWCONSTANTS_H_STP_POST_ENABLE_DELAY);
  #endif

  
  #ifdef __HWCONSTANTS_H_USE_STEPPER_DRIVER
  #ifdef __HWCONSTANTS_H_INVERT_STEPPER_DIRECTION
  // Step forwards or backwards
  if (step_size < 0) {
    nondirectional_steps = -step_size * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, HIGH);
  } else {
    nondirectional_steps = step_size * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, LOW);
  }  
  #endif
  
  #ifndef __HWCONSTANTS_H_INVERT_STEPPER_DIRECTION
  // Step forwards or backwards
  if (step_size < 0) {
    nondirectional_steps = -step_size * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, LOW);
  } else {
    nondirectional_steps = step_size * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, HIGH);
  }    
  #endif
  #endif


  // iterate till target found
  while (keep_going)
  {
    // Rotate the correct number of steps
    #ifdef __HWCONSTANTS_H_USE_STEPPER_DRIVER
    for (int i=0; i<nondirectional_steps; i++) {
      rotate_one_step();
    }
    #endif
    
    #ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
    stimStepper->step(step_size);
    #endif
    
    actual_steps += step_size;
    
    // update sensor and store previous value
    prev_sensor = sensor;
    if (hall_sensor_id == 1) {
      sensor = analogRead(__HWCONSTANTS_H_HALL1);
    } else if (hall_sensor_id == 2) {
      sensor = analogRead(__HWCONSTANTS_H_HALL2);
    }

    // Store in circular buffer
    sensor_history[sensor_history_idx] = sensor;
    sensor_history_idx = (sensor_history_idx + 1) % 
      __HWCONSTANTS_H_SENSOR_HISTORY_SZ;    
    
    // test if peak found
    if (positive_peak && (prev_sensor > (512 + __HWCONSTANTS_H_HALL_THRESH)) && ((sensor - prev_sensor) < -2))
    {
        // Positive peak: sensor is high, but decreasing
        keep_going = 0;
    }
    else if (!positive_peak && (prev_sensor < (512 - __HWCONSTANTS_H_HALL_THRESH)) && ((sensor - prev_sensor) > 2))
    {
        // Negative peak: sensor is low, but increasing
        keep_going = 0;
    }
    
    // Quit if >400 steps have been taken
    if (abs(actual_steps) > 400) {
      Serial.print(millis());
      Serial.println(" DBG STEPS400");
      keep_going = 0;
    }
  }

  // Dump the circular buffer
  Serial.print(millis());
  Serial.print(" SENH ");
  for (int i=0; i<__HWCONSTANTS_H_SENSOR_HISTORY_SZ; i++) {
    Serial.print(sensor_history[
      (sensor_history_idx + i + 1) % __HWCONSTANTS_H_SENSOR_HISTORY_SZ]);
    Serial.print(" ");
  }
  Serial.println("");

  // Undo the last step to reach peak exactly
  #ifdef __HWCONSTANTS_H_USE_STEPPER_DRIVER
  #ifdef __HWCONSTANTS_H_INVERT_STEPPER_DIRECTION
  // Step forwards or backwards
  if (step_size < 0) {
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, LOW);
  } else {
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, HIGH);
  }  
  #endif
  
  #ifndef __HWCONSTANTS_H_INVERT_STEPPER_DIRECTION
  // Step forwards or backwards
  if (step_size < 0) {
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, HIGH);
  } else {
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, LOW);
  }    
  #endif
  
  rotate_one_step();
  #endif
  
  
  // Disable H-bridge to prevent overheating
  #ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
  digitalWrite(TWOPIN_ENABLE_STEPPER, LOW);
  #endif

  // update to specified position
  sticky_stepper_position = set_position;

  return actual_steps;
}

int rotate(long n_steps)
{ /* Low-level rotation function 
  
  I think positive n_steps means CCW and negative n_steps means CW. It does
  on L2, at least.
  */
  
  
  #ifdef __HWCONSTANTS_H_USE_STEPPER_DRIVER
  // This incorporates microstepping and will always be positive
  long nondirectional_steps = 0;
  
  #ifdef __HWCONSTANTS_H_INVERT_STEPPER_DIRECTION
  // Step forwards or backwards
  if (n_steps < 0) {
    nondirectional_steps = -n_steps * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, HIGH);
  } else {
    nondirectional_steps = n_steps * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, LOW);
  }  
  #endif
  
  #ifndef __HWCONSTANTS_H_INVERT_STEPPER_DIRECTION
  // Step forwards or backwards
  if (n_steps < 0) {
    nondirectional_steps = -n_steps * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, LOW);
  } else {
    nondirectional_steps = n_steps * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, HIGH);
  }    
  #endif
  
  // Rotate the correct number of steps
  for (int i=0; i<nondirectional_steps; i++) {
    rotate_one_step();
  }
  #endif


  #ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
  // Enable the stepper according to the type of setup
  digitalWrite(TWOPIN_ENABLE_STEPPER, HIGH);

  // Sometimes the stepper spins like crazy without a delay here
  delay(__HWCONSTANTS_H_STP_POST_ENABLE_DELAY);
  
  // BLOCKING CALL //
  // Replace this with more iterations of smaller steps
  stimStepper->step(n_steps);

  // Disable H-bridge to prevent overheating
  delay(__HWCONSTANTS_H_STP_POST_ENABLE_DELAY);
  digitalWrite(TWOPIN_ENABLE_STEPPER, LOW);
  #endif
 
 
  // update sticky_stepper_position
  sticky_stepper_position = sticky_stepper_position + n_steps;
  
  // keep it in the range [0, 200)
  sticky_stepper_position = (sticky_stepper_position + 200) % 200;
  
  return 0;
}

#ifdef __HWCONSTANTS_H_USE_STEPPER_DRIVER
void rotate_one_step()
{ // Pulse the step pin, then delay the specified number of microseconds
  digitalWrite(__HWCONSTANTS_H_STEP_PIN, HIGH);
  delayMicroseconds(__HWCONSTANTS_H_STEP_HALFDELAY_US / 
    __HWCONSTANTS_H_MICROSTEP);
  digitalWrite(__HWCONSTANTS_H_STEP_PIN, LOW);
  delayMicroseconds(__HWCONSTANTS_H_STEP_HALFDELAY_US / 
    __HWCONSTANTS_H_MICROSTEP);  
}
#endif



//// StateResponseWindow
void StateResponseWindow::update(uint16_t touched)
{
 my_touched = touched;
}

void StateResponseWindow::loop()
{
  int current_response;
  bool licking_l;
  bool licking_r;
  unsigned long time = millis();
  
  // get the licking state 
  // overridden in FakeResponseWindow
  set_licking_variables(licking_l, licking_r);
  
  // Turn off laser if we've been in the state for long enough
  if ((time - (timer - duration)) > 1000) {
    digitalWrite(__HWCONSTANTS_H_OPTO, 1);
  }
    
  // transition if max rewards reached
  if (my_rewards_this_trial >= param_values[tpidx_MRT])
  {
    next_state = INTER_TRIAL_INTERVAL;
    flag_stop = 1;
    return;
  }

  // Do nothing if both or neither are being licked.
  // Otherwise, assign current_response.
  if (!licking_l && !licking_r)
    return;
  else if (licking_l && licking_r)
    return;
  else if (licking_l && !licking_r)
    current_response = LEFT;
  else if (!licking_l && licking_r)
    current_response = RIGHT;
  else
    Serial.println("ERR this should never happen");

  // Only assign result if this is the first response
  if (results_values[tridx_RESPONSE] == 0)
    results_values[tridx_RESPONSE] = current_response;
  
  // Move to reward state, or error if TOE is set, or otherwise stay
  if ((current_response == LEFT) && (param_values[tpidx_REWSIDE] == LEFT))
  { // Hit on left
    next_state = REWARD_L;
    my_rewards_this_trial++;
    results_values[tridx_OUTCOME] = OUTCOME_HIT;
  }
  else if ((current_response == RIGHT) && (param_values[tpidx_REWSIDE] == RIGHT))
  { // Hit on right
    next_state = REWARD_R;
    my_rewards_this_trial++;
    results_values[tridx_OUTCOME] = OUTCOME_HIT;
  }
  else if (param_values[tpidx_TERMINATE_ON_ERR] == __TRIAL_SPEAK_NO)
  { // Error made, TOE is false
    // Decide how to deal with this non-TOE case
  }
  else
  { // Error made, TOE is true
    next_state = ERROR;

    // The type of error depends on whether it's gonogo or 2AFC
    if (param_values[tpidx_REWSIDE] == NOGO) {
      // Response should have been nogo, so he made a false positive or a spoil
      if (current_response == RIGHT) {
        // Licked when he shouldn't have done anything
        results_values[tridx_OUTCOME] = OUTCOME_ERROR;
      } else {
        // Licked the wrong pipe
        results_values[tridx_OUTCOME] = OUTCOME_SPOIL;
      }
    } else {
      // 2AFC task, so it's an error for licking the wrong way
      results_values[tridx_OUTCOME] = OUTCOME_ERROR;
    }
  }
}

void StateResponseWindow::s_finish()
{
  // Turn off laser, if it was on
  digitalWrite(__HWCONSTANTS_H_OPTO, 1);
  
  // If response is still not set, mark as a nogo response
  if (results_values[tridx_RESPONSE] == 0)
  {
    // The response was nogo
    results_values[tridx_RESPONSE] = NOGO;
    
    // Outcome depends on what he was supposed to do
    if (param_values[tpidx_REWSIDE] == NOGO) {
      // Correctly did nothing on a NOGO trial
      results_values[tridx_OUTCOME] = OUTCOME_HIT;
    } else {
      // If this is a 2AFC task, then this is a spoil.
      // If this is a gonogo task, then this is a miss.
      // No way to tell which is which right now, so just call it a spoil
      // regardless.
      results_values[tridx_OUTCOME] = OUTCOME_SPOIL;
    }

  // In any case the trial is over
  next_state = INTER_TRIAL_INTERVAL;
  }
}

void StateResponseWindow::set_licking_variables(bool &licking_l, bool &licking_r)
{ /* Gets the current licking status from the touched variable for each port */
  licking_l = (get_touched_channel(my_touched, 0) == 1);
  licking_r = (get_touched_channel(my_touched, 1) == 1);    
}


//// StateFakeResponsewindow
// Differs only in that it randomly fakes a response
void StateFakeResponseWindow::set_licking_variables(bool &licking_l, bool &licking_r)
{ /* Fakes a response by randomly choosing lick status for each */
  licking_l = (random(0, 10000) < 3);    
  licking_r = (random(0, 10000) < 3);   
}



bool StateWaitToStartTrial::end_condition() {
  return flag_start_trial;
}

void StateWaitToStartTrial::s_finish() {
   // Announce that we have ended the trial and reset the flag
  Serial.print(millis());
  Serial.println(" TRL_RELEASED");
  flag_start_trial = 0;

  // Proceed to next trial
  next_state = TRIAL_START;
}

void StateTrialStart::run() {
   // turn the backlight off
  digitalWrite(__HWCONSTANTS_H_BACK_LIGHT, LOW);
  delay(133);
  digitalWrite(__HWCONSTANTS_H_BACK_LIGHT, HIGH);    

  // Set up the trial based on received trial parameters
  Serial.print(millis());
  Serial.println(" TRL_START");
  for(int i=0; i < N_TRIAL_PARAMS; i++)
  {
    if (param_report_ET[i]) 
    {
      // Buffered write would be nice here
      Serial.print(millis());
      Serial.print(" TRLP ");
      Serial.print(param_abbrevs[i]);
      Serial.print(" ");
      Serial.println(param_values[i]);
    }
  }

  // Set up trial_results to defaults
  for(int i=0; i < N_TRIAL_RESULTS; i++)
  {
    results_values[i] = default_results_values[i];
  }      
  
  
  //// User-defined code goes here
  // declare the states. Here we're both updating the parameters
  // in case they've changed, and resetting all timers.
  srw = StateResponseWindow(param_values[tpidx_RESP_WIN_DUR]);
  sfrw = StateFakeResponseWindow(param_values[tpidx_RESP_WIN_DUR]);
  state_interrotation_pause = StateInterRotationPause(50);
  state_wait_for_servo_move = StateWaitForServoMove(
    param_values[tpidx_SRV_TRAVEL_TIME]);
  state_inter_trial_interval = StateInterTrialInterval(
    param_values[tpidx_ITI]);
  state_error_timeout = StateErrorTimeout(
    param_values[tpidx_ERROR_TIMEOUT], linServo);

  next_state = ROTATE_STEPPER1;

}

//// Wait for servo move
void StateWaitForServoMove::update(Servo linServo)
{
  // Actually this belongs in the constructor.
  my_linServo = linServo;
}

void StateWaitForServoMove::s_setup()
{
  my_linServo.write(param_values[tpidx_SRVPOS]);
  //~ next_state = ROTATE_STEPPER1;   
}

void StateWaitForServoMove::loop()
{
  unsigned long time = millis();

  // First set opto
  if (
    (param_values[tpidx_OPTO] == __TRIAL_SPEAK_YES) &&
    ((time - timer) > -2000)) {
    digitalWrite(__HWCONSTANTS_H_OPTO, 0);
  }
  
  // Now set direct delivery  
  if ((param_values[tpidx_DIRECT_DELIVERY] == __TRIAL_SPEAK_NO) ||
      (direct_delivery_delivered == 1)) {
    return;
  }
  
  if ((time - timer) > -500) {
    if (param_values[tpidx_REWSIDE] == LEFT) {
      Serial.print(time);
      Serial.println(" EV DDR_L");
      digitalWrite(L_REWARD_VALVE, HIGH);
      delay(param_values[tpidx_REWARD_DUR_L]);
      digitalWrite(L_REWARD_VALVE, LOW); 
    }
    else if (param_values[tpidx_REWSIDE] == RIGHT) {
      Serial.print(time);
      Serial.println(" EV DDR_R");      
      digitalWrite(R_REWARD_VALVE, HIGH);
      delay(param_values[tpidx_REWARD_DUR_R]);
      digitalWrite(R_REWARD_VALVE, LOW); 
    }    
    direct_delivery_delivered = 1;
  }
}

void StateWaitForServoMove::s_finish()
{
  next_state = RESPONSE_WINDOW;   
}

void StateRotateStepper1::run() {
 /* Start rotating the stepper motor.
    
  The first rotation is always the same amount.
  The second rotation later achieves the final position.
  The house light is also turned off now.
  */
  //~ digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, LOW);
  rotate(param_values[tpidx_STEP_FIRST_ROTATION]);
  
  // Rotate randomly +180 or -180 to confuse the subject
  // This should be its own state but let's keep it simple for now
  // Could get this as a trial param
  int steps = random(0, 2);

  // convert to steps, +100 or -100
  steps = steps * 200 - 100;

  // rotate    
  #ifdef EXTRA_180DEG_ROT
  delay(50); // between 1st and intermediate
  rotate(steps);      
  #endif
    
  next_state = INTER_ROTATION_PAUSE;
 
}

void StateRotateStepper2::run() {
 /* The second rotation goes to the final position */
  // Calculate how much more we need to rotate
  long remaining_rotation = param_values[tpidx_STPPOS] - 
    sticky_stepper_position;
  int step_size = 1;
  int actual_steps = remaining_rotation;
  
  digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, LOW);
    
  // Take a shorter negative rotation, if available
  // For instance, to go from 0 to 150, it's better to go -50
  if (remaining_rotation > 100)
    remaining_rotation -= 200;
  
  // convoluted way to determine step_size
  if (remaining_rotation < 0)
    step_size = -1;

  // Perform the rotation
  if (param_values[tpidx_STP_HALL] == __TRIAL_SPEAK_YES)
  {
    // Rotate to sensor if available, otherwise regular rotation
    if (param_values[tpidx_STPPOS] == param_values[tpidx_STP_POSITIVE_STPPOS])
      actual_steps = rotate_to_sensor(step_size, 1, param_values[tpidx_STPPOS], 1);
    
    else if (param_values[tpidx_STPPOS] == 
            ((param_values[tpidx_STP_POSITIVE_STPPOS] + 100) % 200))
      actual_steps = rotate_to_sensor(step_size, 0, param_values[tpidx_STPPOS], 1);
    
    else if (param_values[tpidx_STPPOS] == 199) {
      // Rotate to negative reading on second sensor
      actual_steps = rotate_to_sensor(step_size, 0, param_values[tpidx_STPPOS], 2);    
    
    } else if (param_values[tpidx_STPPOS] == 100) {
      // Rotate to positive reading on second sensor
      actual_steps = rotate_to_sensor(step_size, 1, param_values[tpidx_STPPOS], 2);
    
    } else {
      // no sensor available
      rotate(remaining_rotation);
    }
    
    if (actual_steps != remaining_rotation)
    {
      Serial.print(millis());
      Serial.print(" DBG STPERR ");
      Serial.println(actual_steps - remaining_rotation);
    }
  }
  else
  {
    // This is the old rotation function
    rotate(remaining_rotation);
  }
  
  next_state = MOVE_SERVO;
 
}

//// Interrotation pause
void StateInterRotationPause::s_finish()
{
  next_state = ROTATE_STEPPER2;
}

void StateRewardR::run(unsigned long time) {
  Serial.print(time);
  Serial.println(" EV R_R");      
  digitalWrite(R_REWARD_VALVE, HIGH);
  delay(param_values[tpidx_REWARD_DUR_R]);
  digitalWrite(R_REWARD_VALVE, LOW); 
  next_state = POST_REWARD_PAUSE;
 
}

void StateRewardL::run(unsigned long time) {
  Serial.print(time);
  Serial.println(" EV R_L");
  digitalWrite(L_REWARD_VALVE, HIGH);
  delay(param_values[tpidx_REWARD_DUR_L]);
  digitalWrite(L_REWARD_VALVE, LOW); 
  next_state = POST_REWARD_PAUSE;
 
}

//// Post-reward state
void StatePostRewardPause::s_finish()
{
  next_state = RESPONSE_WINDOW;
}

//// StateErrorTimeout
void StateErrorTimeout::s_finish()
{
  next_state = INTER_TRIAL_INTERVAL;
}

void StateErrorTimeout::s_setup()
{
  // Turn off laser, if it was on
  digitalWrite(__HWCONSTANTS_H_OPTO, 1);
  
  my_linServo.write(param_values[tpidx_SRV_FAR]);
}

//// Inter-trial interval
void StateInterTrialInterval::s_setup()
{
  // Turn off laser, if it was on
  digitalWrite(__HWCONSTANTS_H_OPTO, 1);
    
  // First-time code: Report results
  for(int i=0; i < N_TRIAL_RESULTS; i++)
  {
    Serial.print(time_of_last_call);
    Serial.print(" TRLR ");
    Serial.print(results_abbrevs[i]);
    Serial.print(" ");
    Serial.println(results_values[i]);
  }
}

void StateInterTrialInterval::s_finish()
{
  next_state = WAIT_TO_START_TRIAL;   
}



