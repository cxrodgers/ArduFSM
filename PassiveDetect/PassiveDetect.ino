/* Passive detection task.
*/
#include "chat.h"
#include "hwconstants.h"
#include "mpr121.h"
#include <Wire.h> // also for mpr121
#include <Stepper.h>
#include "TimedState.h"
#include "States.h"
#include "Actions.h"
#include "ArduFSM.h"

//// Standard globals
// flag to remember whether we've received the start next trial signal
bool flag_start_trial = 0;

// params and results
extern char* param_abbrevs[N_TRIAL_PARAMS];
extern long param_values[N_TRIAL_PARAMS];
extern bool param_report_ET[N_TRIAL_PARAMS];
extern char* results_abbrevs[N_TRIAL_RESULTS];
extern long results_values[N_TRIAL_RESULTS];
extern long default_results_values[N_TRIAL_RESULTS];

// state monitor
STATE_TYPE current_state;
STATE_TYPE next_state; 

//// Protocol specific globals
// touched monitor
uint16_t sticky_touched = 0;
uint16_t touched = 0;

// Stepper. We won't assign till we know if it's 2pin or 4pin
Stepper *stimStepper = 0;


void user_setup1()
{ /* Protocol-specific setup code that runs before first communication */

  // MPR121 touch sensor setup
  pinMode(TOUCH_IRQ, INPUT);
  digitalWrite(TOUCH_IRQ, HIGH); //enable pullup resistor
  Wire.begin();
  
  // output pins
  pinMode(L_REWARD_VALVE, OUTPUT);
  pinMode(R_REWARD_VALVE, OUTPUT);
  pinMode(__HWCONSTANTS_H_HOUSE_LIGHT, OUTPUT);
  
  // initialize the house light to ON
  digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, HIGH);
  
  // random number seed
  randomSeed(analogRead(__HWCONSTANTS_H_RANDOM_SEED_INPUT));    
}

void user_setup2()
{ /* Protocol-specific setup code that runs before the first loop */

  // Set up the stepper according to two-pin or four-pin mode
  if (param_values[tpidx_2PSTP] == __TRIAL_SPEAK_YES)
  { // Two-pin mode
    pinMode(TWOPIN_ENABLE_STEPPER, OUTPUT);
    pinMode(TWOPIN_STEPPER_1, OUTPUT);
    pinMode(TWOPIN_STEPPER_2, OUTPUT);
    
    // Make sure it's off    
    digitalWrite(TWOPIN_ENABLE_STEPPER, LOW); 
    
    // Initialize
    stimStepper = new Stepper(__HWCONSTANTS_H_NUMSTEPS, 
      TWOPIN_STEPPER_1, TWOPIN_STEPPER_2);
  }
  else
  { // Four-pin mode
    pinMode(ENABLE_STEPPER, OUTPUT);
    pinMode(PIN_STEPPER1, OUTPUT);
    pinMode(PIN_STEPPER2, OUTPUT);
    pinMode(PIN_STEPPER3, OUTPUT);
    pinMode(PIN_STEPPER4, OUTPUT);
    digitalWrite(ENABLE_STEPPER, LOW); // # Make sure it's off
    
    stimStepper = new Stepper(__HWCONSTANTS_H_NUMSTEPS, 
      PIN_STEPPER1, PIN_STEPPER2, PIN_STEPPER3, PIN_STEPPER4);
  }
  
  // thresholds for MPR121
  mpr121_setup(TOUCH_IRQ, param_values[tpidx_TOU_THRESH], 
    param_values[tpidx_REL_THRESH]);

  // Set the speed of the stepper
  stimStepper->setSpeed(param_values[tpidx_STEP_SPEED]);  
}

void user_every_loop()
{
  // Poll touch inputs
  touched = pollTouchInputs();
  
  // announce sticky
  if (touched != sticky_touched)
  {
    Serial.print(time);
    Serial.print(" TCH ");
    Serial.println(touched);
    sticky_touched = touched;
  }  
}

//// Loop function
void loop()
{ /* Called over and over again. On each call, the behavior is determined
     by the current state.
  */
  
  //// Variable declarations
  // get the current time as early as possible in this function
  unsigned long time = millis();

  // statics 
  // these are just "declared" here, they can be modified at the beginning
  // of each trial
  static STATE_TYPE current_state = WAIT_TO_START_TRIAL;
  static StateResponseWindow srw(param_values[tpidx_RESP_WIN_DUR]);
  static StateInterTrialInterval state_inter_trial_interval(
    param_values[tpidx_ITI]);
  static StatePostRewardPause state_post_reward_pause(
        param_values[tpidx_INTER_REWARD_INTERVAL]);

  // The next state, by default the same as the current state
  next_state = current_state;

  // misc
  int status = 1;
  
  //// Run communications
  status = communications(time);
  
  //// User protocol code
  user_every_loop();

  //// Begin state-dependent operations
  // The relevant state function or object is called for the current state.
  // next_state will be set
  // TODO: have it return next_state instead of setting
  // TODO: make each state an object so we can just do next_state.run(time)
  switch (current_state)
  {
    //// Wait till the trial is released. Same for all protocols.
    case WAIT_TO_START_TRIAL:
      state_function_wait_to_start_trial(time);
      break;

    //// TRIAL_START. Same for all protocols.
    case TRIAL_START:
      state_function_trial_start(time);
      break;
  
    // Protocol-specific states
    case MOVE_STEPPER1:
      state_move_stepper1(next_state);
      break;

    case RESPONSE_WINDOW:
      state_function_response_window(time, touched);
      break;
    
    case REWARD_L:
      state_function_reward_l(time);
      break;
    
    case POST_REWARD_PAUSE:
      state_post_reward_pause.run(time);
      break;    

    // Standard inter trial interval state that announces trial results
    case INTER_TRIAL_INTERVAL:
      state_function_inter_trial_interval(time);
      break;
    
    // need an else here
  }
  
  //// Update the state variable
  if (next_state != current_state)
  {
    announce_state_change(time, current_state, next_state);
  }
  current_state = next_state;
  
  return;
}

