/*
  * A protocol that rotates the stepper motor to a position designated by the maximum voltage
    of a hall sensor

  * findStepperPeak() sets horizontal_position equal to the position corressponding to the maximum
    voltage

*/

#include "chat.h"
#include "hwconstants.h"
#include <Servo.h>

#ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
#include <Stepper.h>
#endif

#include "States.h"


// Make this true to generate random responses for debugging
#define FAKE_RESPONDER 0

extern char* param_abbrevs[N_TRIAL_PARAMS];
extern long param_values[N_TRIAL_PARAMS];
extern bool param_report_ET[N_TRIAL_PARAMS];


//// Miscellaneous globals
// flag to remember whether we've received the start next trial signal
// currently being used in both setup() and loop() so it can't be staticked
bool flag_start_trial = 0;


//// Declarations
int take_action(char *protocol_cmd, char *argument1, char *argument2);


//// User-defined variables, etc, go here
/// these should all be staticked into loop() 


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

  
  

  #ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
  // Set the speed of the stepper
  stimStepper->setSpeed(param_values[tpidx_STEP_SPEED]);
  #endif

  

  // initial position of the stepper
  sticky_stepper_position = param_values[tpidx_STEP_INITIAL_POS];
  
  // linear servo setup
  linServo.write(param_values[tpidx_SRV_FAR]);
  delay(param_values[tpidx_SERVO_SETUP_T]);

  // find maximum voltage position of stepper
  findStepperPeak();
  delay(300);


  
}



//// Loop function
void loop()
{
  rotate_to_sensor2();
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
