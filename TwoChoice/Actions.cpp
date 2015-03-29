// Implementations of asynchronous actions for SimpleTrialRelease
#include "Actions.h"
#include "Arduino.h"
#include "States.h"
#include "chat.h"
#include "Params.h"
#include "hwconstants.h"
#include "mpr121.h"

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
  mpr121_setup(TOUCH_IRQ, param_values[tpidx_TOU_THRESH], 
    param_values[tpidx_REL_THRESH]);
}

void asynch_action_light_on()
{
  unsigned long time = millis();
  Serial.print(time);
  Serial.println(" EV HLON");
  digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, HIGH);
}
