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

extern STATE_TYPE next_state;

// These should go into some kind of Protocol.h or something
String param_abbrevs[N_TRIAL_PARAMS] = {
  "STPPOS", "MRT", "RWSD", "SRVPOS", "ITI",
  "2PSTP", "SRVFAR", "SRVTT", "RWIN", "IRI",
  "RD_L", "RD_R", "SRVST", "PSW", "TOE",
  "TO", "STPSPD", "STPFR", "STPIP",
  };
long param_values[N_TRIAL_PARAMS] = {
  1, 1, 1, 1, 3000,
  0, 1900, 4500, 45000, 500,
  40, 40, 1000, 1, 1,
  2000, 20, 50, 50,
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
  0, 0, 0, 0,
};
  
String results_abbrevs[N_TRIAL_RESULTS] = {"RESP", "OUTC"};
long results_values[N_TRIAL_RESULTS] = {0, 0};
long default_results_values[N_TRIAL_RESULTS] = {0, 0};

// This should be passed to the necessary function
long sticky_stepper_position = param_values[tpidx_STEP_INITIAL_POS];  


//// State definitions
extern Stepper stimStepper;


//// StateResponseWindow
void StateResponseWindow::update(uint16_t touched, unsigned int rewards_this_trial)
{
 my_touched = touched;
 my_rewards_this_trial = rewards_this_trial;
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
    next_state = PRE_SERVO_WAIT;
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
    results_values[tridx_OUTCOME] = OUTCOME_HIT;
  }
  else if ((current_response == RIGHT) && (param_values[tpidx_REWSIDE] == RIGHT))
  { // Hit on right
    next_state = REWARD_R;
    results_values[tridx_OUTCOME] = OUTCOME_HIT;
  }
  else if (param_values[tpidx_TERMINATE_ON_ERR] == 2)
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


//// Wait for servo move
void StateWaitForServoMove::update(Servo linServo)
{
  // Actually this belongs in the constructor.
  my_linServo = linServo;
}

void StateWaitForServoMove::s_setup()
{
  my_linServo.write(param_values[tpidx_SRVPOS]);
  next_state = ROTATE_STEPPER1;   
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
    Serial.println((String) time_of_last_call + " TRLR " + (String) results_abbrevs[i] + 
      " " + (String) results_values[i]);
  }
}

void StateInterTrialInterval::s_finish()
{
  next_state = WAIT_TO_START_TRIAL;   
}

//// Non-class states
int state_rotate_stepper1(STATE_TYPE& next_state)
{
  rotate(param_values[tpidx_STEP_FIRST_ROTATION]);
  next_state = INTER_ROTATION_PAUSE;
  return 0;    
}

int state_rotate_stepper2(STATE_TYPE& next_state)
{
  int remaining_rotation = param_values[tpidx_STPPOS] - 
    param_values[tpidx_STEP_FIRST_ROTATION] - sticky_stepper_position;
  
  rotate(remaining_rotation);
  
  next_state = WAIT_FOR_SERVO_MOVE;
  return 0;    
}

int rotate(long n_steps)
{
  // rotate_motor(param_values[tpidx_STEP_FIRST_ROTATION], 20);
  if (param_values[tpidx_2PSTP])
  {
    digitalWrite(TWOPIN_ENABLE_STEPPER, HIGH);
  }
  else
  {
    digitalWrite(ENABLE_STEPPER, HIGH);
  }

  
  // BLOCKING CALL //
  // Replace with more iterations of smaller steps
  stimStepper.step(n_steps);


  // disable
  if (param_values[tpidx_2PSTP])
  {
    digitalWrite(TWOPIN_ENABLE_STEPPER, LOW);
  }
  else
  {
    digitalWrite(ENABLE_STEPPER, LOW);
  }    

  
  return 0;
}

// The reward states use delay because they need to be millisecond-precise
int state_reward_l(STATE_TYPE& next_state)
{
  digitalWrite(L_REWARD_VALVE, HIGH);
  delay(param_values[tpidx_REWARD_DUR_L]);
  digitalWrite(L_REWARD_VALVE, LOW); 
  next_state = INTER_TRIAL_INTERVAL;
  return 0;  
}
int state_reward_r(STATE_TYPE& next_state)
{
  digitalWrite(R_REWARD_VALVE, HIGH);
  delay(param_values[tpidx_REWARD_DUR_R]);
  digitalWrite(R_REWARD_VALVE, LOW); 
  next_state = INTER_TRIAL_INTERVAL;
  return 0;  
}
