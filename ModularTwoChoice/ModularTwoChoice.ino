/* A two-alternative choice behavior with left and right lick ports.

TODO
----
* Move the required states, like TRIAL_START and WAIT_FOR_NEXT_TRIAL,
  as well as all required variables like flag_start_trial, into TrialSpeak.cpp.
* move definitions of trial_params to header file, so can be auto-generated
* diagnostics: which state it is in on each call (or subset of calls)

Here are the things that the user should have to change for each protocol:
* Enum of states
* User-defined states in switch statement
* param_abbrevs, param_values, tpidx_*, N_TRIAL_PARAMS
*/
#include "chat.h"
#include "hwconstants.h"
#include <Servo.h>

#ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
#include <Stepper.h>
#endif

#include "TimedState.h"
#include "States.h"

#ifndef __HWCONSTANTS_H_USE_IR_DETECTOR
#include "mpr121.h"
#include <Wire.h> // also for mpr121
#endif

#ifdef __HWCONSTANTS_H_USE_IR_DETECTOR
#include "ir_detector.h"
#endif

// Make this true to generate random responses for debugging
#define FAKE_RESPONDER 0

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

// initial position of stim arm .. user must ensure this is correct
extern long sticky_stepper_position;


/// not sure how to static these since they are needed by both loop and setup
// Servo
Servo linServo;

// Stepper
// We won't assign till we know if it's 2pin or 4pin
#ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
Stepper *stimStepper = 0;
#endif

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
  #ifndef __HWCONSTANTS_H_USE_IR_DETECTOR
  pinMode(TOUCH_IRQ, INPUT);
  digitalWrite(TOUCH_IRQ, HIGH); //enable pullup resistor
  Wire.begin();
  #endif
  
  // output pins
  pinMode(L_REWARD_VALVE, OUTPUT);
  pinMode(R_REWARD_VALVE, OUTPUT);
  pinMode(__HWCONSTANTS_H_HOUSE_LIGHT, OUTPUT);
  pinMode(__HWCONSTANTS_H_BACK_LIGHT, OUTPUT);
  
  // initialize the house light to ON
  digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, HIGH);
  digitalWrite(__HWCONSTANTS_H_BACK_LIGHT, HIGH);
  
  // random number seed
  randomSeed(analogRead(3));

  // attach servo
  linServo.attach(LINEAR_SERVO);
  //linServo.write(1850); // move close for measuring

  
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



  #ifdef __HWCONSTANTS_H_USE_STEPPER_DRIVER
  pinMode(__HWCONSTANTS_H_STEP_ENABLE, OUTPUT);
  pinMode(__HWCONSTANTS_H_STEP_PIN, OUTPUT);
  pinMode(__HWCONSTANTS_H_STEP_DIR, OUTPUT);
  
  // Make sure it's off    
  digitalWrite(__HWCONSTANTS_H_STEP_ENABLE, LOW); 
  digitalWrite(__HWCONSTANTS_H_STEP_PIN, LOW);
  digitalWrite(__HWCONSTANTS_H_STEP_DIR, LOW);  
  #endif
  
  #ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
  pinMode(TWOPIN_ENABLE_STEPPER, OUTPUT);
  pinMode(TWOPIN_STEPPER_1, OUTPUT);
  pinMode(TWOPIN_STEPPER_2, OUTPUT);
  
  // Make sure it's off    
  digitalWrite(TWOPIN_ENABLE_STEPPER, LOW); 
  
  // Initialize
  stimStepper = new Stepper(__HWCONSTANTS_H_NUMSTEPS, 
    TWOPIN_STEPPER_1, TWOPIN_STEPPER_2);
  #endif


  // Opto (collides with one of the 4-pin setups)
  pinMode(__HWCONSTANTS_H_OPTO, OUTPUT);
  digitalWrite(__HWCONSTANTS_H_OPTO, HIGH);
  
  
  // thresholds for MPR121
  #ifndef __HWCONSTANTS_H_USE_IR_DETECTOR
  mpr121_setup(TOUCH_IRQ, param_values[tpidx_TOU_THRESH], 
    param_values[tpidx_REL_THRESH]);
  #endif


  #ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
  // Set the speed of the stepper
  stimStepper->setSpeed(param_values[tpidx_STEP_SPEED]);
  #endif


  // initial position of the stepper
  sticky_stepper_position = param_values[tpidx_STEP_INITIAL_POS];
  
  // linear servo setup
  linServo.write(param_values[tpidx_SRV_FAR]);
  delay(param_values[tpidx_SERVO_SETUP_T]);
}



//// Loop function
void loop()
{ /* Called over and over again. On each call, the behavior is determined
     by the current state.
  */
  
  //// Variable declarations
  // get the current time as early as possible in this function
  unsigned long time = millis();
  static STATE_TYPE current_state = WAIT_TO_START_TRIAL;


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
  #ifndef __HWCONSTANTS_H_USE_IR_DETECTOR
  touched = pollTouchInputs();
  #endif
  
  #ifdef __HWCONSTANTS_H_USE_IR_DETECTOR
  if (time % 500 == 0) {
    touched = pollTouchInputs(time, 1);
  } else {
    touched = pollTouchInputs(time, 0);
  }
  #endif
  
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
  stateDependentOperations(current_state, time);
  
  
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


//// Take protocol action based on user command (ie, setting variable)
int take_action(char *protocol_cmd, char *argument1, char *argument2)
{ /* Protocol action.
  
  Currently two possible actions:
    if protocol_cmd == 'SET':
      argument1 is the variable name. argument2 is the data.
    if protocol_cmd == 'ACT':
      argument1 is converted into a function based on a dispatch table.
        REWARD_L : reward the left valve
        REWARD_R : reward the right valve
        REWARD : reward the current valve

  This logic could be incorporated in TrialSpeak, but we would need to provide
  the abbreviation, full name, datatype, and optional handling logic for
  each possible variable. So it seems to make more sense here.
  
  Return values:
  0 - command parsed successfully
  2 - unimplemented protocol_cmd
  4 - unknown variable on SET command
  5 - data conversion error
  6 - unknown asynchronous action
  */
  int status;
  
  //~ Serial.print("DBG take_action ");
  //~ Serial.print(protocol_cmd);
  //~ Serial.print("-");
  //~ Serial.print(argument1);
  //~ Serial.print("-");
  //~ Serial.println(argument2);
  
  if (strncmp(protocol_cmd, "SET\0", 4) == 0)
  {
    // Find index into param_abbrevs
    int idx = -1;
    for (int i=0; i < N_TRIAL_PARAMS; i++)
    {
      if (strcmp(param_abbrevs[i], argument1) == 0)
      {
        idx = i;
        break;
      }
    }
    
    // Error if not found, otherwise set
    if (idx == -1)
    {
      Serial.print("ERR param not found ");
      Serial.println(argument1);
      return 4;
    }
    else
    {
      // Convert to int
      status = safe_int_convert(argument2, param_values[idx]);

      // Debug
      //~ Serial.print("DBG setting var ");
      //~ Serial.print(idx);
      //~ Serial.print(" to ");
      //~ Serial.println(argument2);

      // Error report
      if (status != 0)
      {
        Serial.println("ERR can't set var");
        return 5;
      }
    }
  }   

  else if (strncmp(protocol_cmd, "ACT\0", 4) == 0)
  {
    // Dispatch
    if (strncmp(argument1, "REWARD_L\0", 9) == 0) {
      asynch_action_reward_l();
    } else if (strncmp(argument1, "REWARD_R\0", 9) == 0) {
      asynch_action_reward_r();
    } else if (strncmp(argument1, "REWARD\0", 7) == 0) {
      asynch_action_reward();
    } else if (strncmp(argument1, "THRESH\0", 7) == 0) {
      asynch_action_set_thresh();
    } else if (strncmp(argument1, "HLON\0", 5) == 0) {
      asynch_action_light_on();
    } 
    else
      return 6;
  }      
  else
  {
    // unknown command
    return 2;
  }
  return 0;
}


int safe_int_convert(char *string_data, long &variable)
{ /* Check that string_data can be converted to long before setting variable.
  
  Returns 1 if string data could not be converted to %d.
  */
  long conversion_var = 0;
  int status;
  
  // Parse into %d
  // Returns number of arguments successfully parsed
  status = sscanf(string_data, "%ld", &conversion_var);
    
  //~ Serial.print("DBG SIC ");
  //~ Serial.print(string_data);
  //~ Serial.print("-");
  //~ Serial.print(conversion_var);
  //~ Serial.print("-");
  //~ Serial.print(status);
  //~ Serial.println(".");
  
  if (status == 1) {
    // Good, we converted one variable
    variable = conversion_var;
    return 0;
  }
  else {
    // Something went wrong, probably no variables converted
    Serial.print("ERR SIC cannot parse -");
    Serial.print(string_data);
    Serial.println("-");
    return 1;
  }
}


void asynch_action_reward_l()
{
  unsigned long time = millis();
  Serial.print(time);
  Serial.println(" EV AAR_L");
  digitalWrite(L_REWARD_VALVE, HIGH);
  delay(param_values[tpidx_REWARD_DUR_L]);
  digitalWrite(L_REWARD_VALVE, LOW); 
}

void asynch_action_reward_r()
{
  unsigned long time = millis();
  Serial.print(time);
  Serial.println(" EV AAR_R");
  digitalWrite(R_REWARD_VALVE, HIGH);
  delay(param_values[tpidx_REWARD_DUR_R]);
  digitalWrite(R_REWARD_VALVE, LOW); 
}

void asynch_action_reward()
{
  if (param_values[tpidx_REWSIDE] == LEFT)
    asynch_action_reward_l();
  else if (param_values[tpidx_REWSIDE] == RIGHT)
    asynch_action_reward_r();
  else
    Serial.println("ERR unknown rewside");
}

void asynch_action_set_thresh()
{
  unsigned long time = millis();
  Serial.print(time);
  Serial.println(" EV AAST");

  #ifndef __HWCONSTANTS_H_USE_IR_DETECTOR
  mpr121_setup(TOUCH_IRQ, param_values[tpidx_TOU_THRESH], 
    param_values[tpidx_REL_THRESH]);
  #endif
}

void asynch_action_light_on()
{
  unsigned long time = millis();
  Serial.print(time);
  Serial.println(" EV HLON");
  digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, HIGH);
}
