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


extern char* param_abbrevs[N_TRIAL_PARAMS];
extern long param_values[N_TRIAL_PARAMS];
extern bool param_report_ET[N_TRIAL_PARAMS];
extern char* results_abbrevs[N_TRIAL_RESULTS];
extern long results_values[N_TRIAL_RESULTS];
extern long default_results_values[N_TRIAL_RESULTS];

//// Miscellaneous globals
// flag to remember whether we've received the start next trial signal
// currently being used in both setup() and loop() so it can't be staticked
bool flag_start_trial = 0;


//// Declarations
int take_action(char *protocol_cmd, char *argument1, char *argument2);


//// User-defined variables, etc, go here
/// these should all be staticked into loop()
STATE_TYPE next_state; 

// touched monitor
uint16_t sticky_touched = 0;

/// not sure how to static these since they are needed by both loop and setup
// Stepper
// We won't assign till we know if it's 2pin or 4pin
Stepper *stimStepper = 0;

//// Setup function
void setup()
{
  unsigned long time = millis();
  int status = 1;
  
  Serial.begin(115200);
  Serial.print(time);
  Serial.println(" DBG begin setup");

  //// Begin user protocol code
  //// Put this in a user_setup1() function?
  
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
  randomSeed(analogRead(3));

  //// Run communications until we've received all setup info
  // Later make this a new flag. For now wait for first trial release.
  while (!flag_start_trial)
  {
    status = communications(time);
    if (status != 0)
    {
      Serial.println("comm error in setup");
      delay(1000);
    }
  }
  
  
  //// Now finalize the setup using the received initial parameters
  // user_setup2() function?
  
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
  
  //// User protocol variables
  uint16_t touched = 0;
  
  
  //// Run communications
  status = communications(time);
  
  
  //// User protocol code
  // could put other user-specified every_loop() stuff here
  
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
  
  //// Begin state-dependent operations
  // Try to replace every case with a single function or object call
  // Ultimately this could be a dispatch table.
  // Also, eventually we'll probably want them to return next_state,
  // but currently it's generally passed by reference.
  switch (current_state)
  {
    //// Wait till the trial is released. Same for all protocols.
    case WAIT_TO_START_TRIAL:
      // Wait until we receive permission to continue  
      if (flag_start_trial)
      {
        // Announce that we have ended the trial and reset the flag
        Serial.print(time);
        Serial.println(" TRL_RELEASED");
        flag_start_trial = 0;
        
        // Proceed to next trial
        next_state = TRIAL_START;
      }
      break;

    //// TRIAL_START. Same for all protocols.
    case TRIAL_START:
      // Set up the trial based on received trial parameters
      Serial.print(time);
      Serial.println(" TRL_START");
      for(int i=0; i < N_TRIAL_PARAMS; i++)
      {
        if (param_report_ET[i]) 
        {
          // Buffered write would be nice here
          Serial.print(time);
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
      state_inter_trial_interval = StateInterTrialInterval(
        param_values[tpidx_ITI]);

      
      next_state = MOVE_STEPPER1;
      break;

    case MOVE_STEPPER1:
      state_move_stepper1(next_state);
      break;

    case RESPONSE_WINDOW:
      srw.update(touched);
      srw.run(time);
      break;
    
    case REWARD_L:
      Serial.print(time);
      Serial.println(" EV R_L");
      state_reward_l(next_state);
      break;
    
    case POST_REWARD_PAUSE:
      state_post_reward_pause.run(time);
      break;    

    case INTER_TRIAL_INTERVAL:
      // turn the light on
      digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, HIGH);
      
      // Announce trial_results
      state_inter_trial_interval.run(time);
      break;
    
    // need an else here
  }
  
  
  //// Update the state variable
  if (next_state != current_state)
  {
      
    Serial.print(time);
    Serial.print(" ST_CHG ");
    Serial.print(current_state);
    Serial.print(" ");
    Serial.println(next_state);
    
    Serial.print(millis());
    Serial.print(" ST_CHG2 ");
    Serial.print(current_state);
    Serial.print(" ");
    Serial.println(next_state);
  }
  current_state = next_state;
  
  return;
}

