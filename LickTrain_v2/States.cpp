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

// include this one just to get __TRIAL_SPEAK_YES
#include "chat.h"

extern STATE_TYPE next_state;

// These should go into some kind of Protocol.h or something
char* param_abbrevs[N_TRIAL_PARAMS] = {
  "MRT", "RWSD", "IRI", "RD_L", "RD_R",  
  "TOUT", "RELT", "RWIN"
  };
long param_values[N_TRIAL_PARAMS] = {
  1, 1, 500, 40, 40,
  6, 3, 45000
  };

// Whether to report on each trial  
// Currently, manually match this up with Python-side
// Later, maybe make this settable by Python, and default to all True
// Similarly, find out which are required on each trial, and error if they're
// not set. Currently all that are required_ET are also reported_ET.
bool param_report_ET[N_TRIAL_PARAMS] = {
  1, 1, 0, 0, 0,
  0, 0, 0
};

char* results_abbrevs[N_TRIAL_RESULTS] = {"RESP", "OUTC"};
long results_values[N_TRIAL_RESULTS] = {0, 0};
long default_results_values[N_TRIAL_RESULTS] = {0, 0};

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
    if (results_values[tridx_OUTCOME] == 0) {
      results_values[tridx_OUTCOME] = OUTCOME_HIT;
    }
  }
  else if ((current_response == RIGHT) && (param_values[tpidx_REWSIDE] == RIGHT))
  { // Hit on right
    next_state = REWARD_R;
    if (results_values[tridx_OUTCOME] == 0) {
      results_values[tridx_OUTCOME] = OUTCOME_HIT;
    }
  }
  else
  { // Error made. Set outcome if not set already
    if (results_values[tridx_OUTCOME] == 0) {
        results_values[tridx_OUTCOME] = OUTCOME_ERROR;
    }
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
