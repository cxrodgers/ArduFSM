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
  "NSTPS", "MRT", "ITI", "2PSTP", "RWIN", 
  "IRI", "RD_L", "RD_R", "STPSPD", "TOUT", 
  "RELT", "STPT", "ISGO",
  };
  
long param_values[N_TRIAL_PARAMS] = {
  3, 1, 3000, 3, 2000,
  500, 50, 50, 20, 6,
  6, 10, 3
  };

// Whether to report on each trial  
// Currently, manually match this up with Python-side
// Later, maybe make this settable by Python, and default to all True
// Similarly, find out which are required on each trial, and error if they're
// not set. Currently all that are required_ET are also reported_ET.
bool param_report_ET[N_TRIAL_PARAMS] = {
  1, 0, 1, 0, 0,
  0, 0, 0, 0, 0,
  0, 0, 1
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

  // Normally we check if response was already set, but for GO/NOGO this
  // is not necessary.
  // Move to reward state, or error if TOE is set, or otherwise stay
  if ((current_response == LEFT) && (param_values[tpidx_ISGO] == __TRIAL_SPEAK_YES))
  { // Hit on go
    next_state = REWARD_L;
    my_rewards_this_trial++;
    results_values[tridx_OUTCOME] = OUTCOME_HIT;
    results_values[tridx_RESPONSE] = LEFT;
  }
  else if ((current_response == LEFT) && (param_values[tpidx_ISGO] == __TRIAL_SPEAK_NO))
  { // Error on nogo
    results_values[tridx_OUTCOME] = OUTCOME_ERROR;
    results_values[tridx_RESPONSE] = LEFT;
  }
}

void StateResponseWindow::s_finish()
{
  // If response is still not set
  if (results_values[tridx_RESPONSE] == 0) {
    // Mark response as NOGO
    results_values[tridx_RESPONSE] = NOGO;
    
    // Mark outcome to correct if it was a nogo trial
    if ((param_values[tpidx_ISGO] == __TRIAL_SPEAK_YES)) {
      // error on go
      results_values[tridx_OUTCOME] = OUTCOME_ERROR;
    } else {
      // hit on nogo
      results_values[tridx_OUTCOME] = OUTCOME_HIT;
    }
  }
  next_state = INTER_TRIAL_INTERVAL;

}

void StateResponseWindow::set_licking_variables(bool &licking_l, bool &licking_r)
{ /* Gets the current licking status from the touched variable for each port */
  licking_l = (get_touched_channel(my_touched, 0) == 1);
  licking_r = (get_touched_channel(my_touched, 1) == 1);    
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
int state_move_stepper1(STATE_TYPE& next_state)
{ /* Move the stepper motor, or don't. */
  
  // Depends on whether go trial or not  
  if (param_values[tpidx_ISGO] == __TRIAL_SPEAK_YES) {
    Serial.println("0 DBG moving");
    // Go trial: move, delay, move back
    rotate(param_values[tpidx_NSTPS]);
    delay(param_values[tpidx_STPT]);
    rotate(-param_values[tpidx_NSTPS]);
  } else {
    // Nogo trial: try to match the delay
    Serial.println("0 DBG not moving");
    delay(param_values[tpidx_STPT]);
  }

  next_state = RESPONSE_WINDOW;
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
  delay(__HWCONSTANTS_H_STP_POST_ENABLE_DELAY);
  
  // BLOCKING CALL //
  // Replace this with more iterations of smaller steps
  stimStepper->step(n_steps);

  // This delay doesn't seem necessary
  //delay(50);
  
  // disable
  if (param_values[tpidx_2PSTP] == __TRIAL_SPEAK_YES)
    digitalWrite(TWOPIN_ENABLE_STEPPER, LOW);
  else
    digitalWrite(ENABLE_STEPPER, LOW);

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


/* Required protocol specific functions */
void user_trial_start(unsingned long time)
{  /* Protocol-specific code that runs at trial start */
  // declare the states. Here we're both updating the parameters
  // in case they've changed, and resetting all timers.
  srw = StateResponseWindow(param_values[tpidx_RESP_WIN_DUR]);
  state_inter_trial_interval = StateInterTrialInterval(
    param_values[tpidx_ITI]);

  next_state = MOVE_STEPPER1;
}


/* State functions */
void state_function_response_window(unsigned long time, uint16_t touched) {
  srw.update(touched);
  srw.run(time);
}

void state_function_reward_l(unsigned long time) {
  Serial.print(time);
  Serial.println(" EV R_L");
  state_reward_l();  
}

void state_function_inter_trial_interval(unsigned long time) {
  // turn the light on
  digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, HIGH);
  
  // Announce trial_results
  state_inter_trial_interval.run(time);
}

