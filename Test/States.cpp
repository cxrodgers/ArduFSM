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
#include "Params.h"
#include "TrialSpeak.h"
#include "ArduFSM.h"

// include this one just to get __TRIAL_SPEAK_YES
#include "chat.h"

// Params
// params and results
extern char* param_abbrevs[N_TRIAL_PARAMS];
extern long param_values[N_TRIAL_PARAMS];
extern bool param_report_ET[N_TRIAL_PARAMS];
extern char* results_abbrevs[N_TRIAL_RESULTS];
extern long results_values[N_TRIAL_RESULTS];
extern long default_results_values[N_TRIAL_RESULTS];



// Global, persistent variable to remember where the stepper is
long sticky_stepper_position = 0;


//// State definitions
extern Stepper* stimStepper;


// Standard states
extern StateTrialStart state_trial_start;
extern StateWaitToStartTrial state_wait_to_start_trial;

// Define all the states that we are going to use
StateInterTrialInterval state_inter_trial_interval(
    param_values[tpidx_ITI]);
StateRotateStepper1 state_rotate_stepper1;


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

State* StateInterTrialInterval::s_finish()
{
  return &state_wait_to_start_trial;
}

//// Non-class states
State* StateRotateStepper1::run(unsigned long time) 
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

  return &state_inter_trial_interval;
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


/* Required protocol specific functions */
State* user_trial_start()
{  /* Protocol-specific code that runs at trial start */
  // declare the states. Here we're both updating the parameters
  // in case they've changed, and resetting all timers.
  state_inter_trial_interval = StateInterTrialInterval(
    param_values[tpidx_ITI]);

  return &state_rotate_stepper1;
}



