/* Implementation file for declaring protocol-specific states.
This implements a two-alternative choice task with two lick ports.

Defines the following:
* param_abbrevs, which defines the shorthand for the trial parameters
* param_values, which define the defaults for those parameters
* results_abbrevs, results_values, default_results_values
* implements the state functions and state objects

*/

#include "States.h"
#include "mpr121.h"
#include "Arduino.h"
#include "hwconstants.h"
#include "Stepper.h"

// include this one just to get __TRIAL_SPEAK_YES
#include "chat.h"

extern STATE_TYPE next_state;

// These should go into some kind of Protocol.h or something
char* param_abbrevs[N_TRIAL_PARAMS] = {
  "STPPOS", "MRT", "RWSD", "SRVPOS", "ITI",
  "2PSTP", "SRVFAR", "SRVTT", "RWIN", "IRI",
  "RD_L", "RD_R", "SRVST", "PSW", "TOE",
  "TO", "STPSPD", "STPFR", "STPIP", "ISRND",
  "TOUT", "RELT"
  };
long param_values[N_TRIAL_PARAMS] = {
  1, 1, 1, 1, 3000,
  0, 1900, 4500, 45000, 500,
  40, 40, 1000, 1, 1,
  6000, 20, 50, 50, 0,
  6, 3
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
  0, 0
};
  
char* results_abbrevs[N_TRIAL_RESULTS] = {"RESP", "OUTC"};
long results_values[N_TRIAL_RESULTS] = {0, 0};
long default_results_values[N_TRIAL_RESULTS] = {0, 0};

// Global, persistent variable to remember where the stepper is
long sticky_stepper_position = 0;


//// State definitions
extern Stepper* stimStepper;


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
  
  // get the licking state 
  // overridden in FakeResponseWindow
  set_licking_variables(licking_l, licking_r);
  
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
    results_values[tridx_OUTCOME] = OUTCOME_ERROR;
  }
}

void StateResponseWindow::s_finish()
{
  // If response is still not set, mark as spoiled
  if (results_values[tridx_RESPONSE] == 0)
  {
    results_values[tridx_RESPONSE] = NOGO;
    results_values[tridx_OUTCOME] = OUTCOME_SPOIL;
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


//// Interrotation pause
void StateInterRotationPause::s_finish()
{
  next_state = ROTATE_STEPPER2;
}


//// StateErrorTimeout
void StateErrorTimeout::s_finish()
{
  next_state = INTER_TRIAL_INTERVAL;
}

void StateErrorTimeout::s_setup()
{
  my_linServo.write(param_values[tpidx_SRV_FAR]);
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

void StateWaitForServoMove::s_finish()
{
  next_state = RESPONSE_WINDOW;   
}

//// Inter-trial interval
void StateInterTrialInterval::s_setup()
{
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

//// Non-class states
int state_rotate_stepper1(STATE_TYPE& next_state)
{ /* Start rotating the stepper motor.
    
  The first rotation is always the same amount.
  The second rotation later achieves the final position.
  The house light is also turned off now.
  */
  digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, LOW);
  rotate(param_values[tpidx_STEP_FIRST_ROTATION]);
  next_state = INTER_ROTATION_PAUSE;
  return 0;    
}

int state_rotate_stepper2(STATE_TYPE& next_state)
{ /* The second rotation goes to the final position */
  // Calculate how much more we need to rotate
  long remaining_rotation = param_values[tpidx_STPPOS] - 
    sticky_stepper_position;
  
  // Take a shorter negative rotation, if available
  // For instance, to go from 0 to 150, it's better to go -50
  if (remaining_rotation > 100)
    remaining_rotation -= 200;
    
  // Do it
  rotate(remaining_rotation);
  
  next_state = MOVE_SERVO;
  return 0;    
}
  


int rotate(long n_steps)
{ /* Low-level rotation function 
  
  I think positive n_steps means CCW and negative n_steps means CW. It does
  on L2, at least.
  */

  // Enable the stepper according to the type of setup
  if (param_values[tpidx_2PSTP] == __TRIAL_SPEAK_YES)
    digitalWrite(TWOPIN_ENABLE_STEPPER, HIGH);
  else
    digitalWrite(ENABLE_STEPPER, HIGH);

  // Sometimes the stepper spins like crazy without a delay here
  delay(100);
  
  // BLOCKING CALL //
  // Replace this with more iterations of smaller steps
  stimStepper->step(n_steps);

  // This delay doesn't seem necessary
  //delay(100);
  
  // disable
  if (param_values[tpidx_2PSTP] == __TRIAL_SPEAK_YES)
    digitalWrite(TWOPIN_ENABLE_STEPPER, LOW);
  else
    digitalWrite(ENABLE_STEPPER, LOW);
  
  // update sticky_stepper_position
  sticky_stepper_position = sticky_stepper_position + n_steps;
  
  // keep it in the range [0, 200)
  sticky_stepper_position = (sticky_stepper_position + 200) % 200;
  
  
  return 0;
}

//// Post-reward state
void StatePostRewardPause::s_finish()
{
  next_state = RESPONSE_WINDOW;
}

// The reward states use delay because they need to be millisecond-precise
int state_reward_l(STATE_TYPE& next_state)
{
  digitalWrite(L_REWARD_VALVE, HIGH);
  delay(param_values[tpidx_REWARD_DUR_L]);
  digitalWrite(L_REWARD_VALVE, LOW); 
  next_state = POST_REWARD_PAUSE;
  return 0;  
}
int state_reward_r(STATE_TYPE& next_state)
{
  digitalWrite(R_REWARD_VALVE, HIGH);
  delay(param_values[tpidx_REWARD_DUR_R]);
  digitalWrite(R_REWARD_VALVE, LOW); 
  next_state = POST_REWARD_PAUSE;
  return 0;  
}
