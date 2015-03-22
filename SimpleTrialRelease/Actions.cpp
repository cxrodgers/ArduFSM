// Implementations of asynchronous actions for SimpleTrialRelease
#include "Actions.h"
#include "Arduino.h"
#include "States.h"
#include "chat.h"
#include "Params.h"


//// Take protocol action based on user command (ie, setting variable)
int take_action(char *protocol_cmd, char *argument1, char *argument2)
{ /* Protocol action.
  
  Boiler plate take_action function that accepts no actions other than SET.
  
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

  //~ else if (strncmp(protocol_cmd, "ACT\0", 4) == 0)
  //~ {
    //~ // Dispatch
    //~ if (strncmp(argument1, "REWARD_L\0", 9) == 0) {
      //~ asynch_action_reward_l();
    //~ } else if (strncmp(argument1, "REWARD_R\0", 9) == 0) {
      //~ asynch_action_reward_r();
    //~ } else if (strncmp(argument1, "THRESH\0", 7) == 0) {
      //~ asynch_action_set_thresh();
    //~ } else if (strncmp(argument1, "HLON\0", 5) == 0) {
      //~ asynch_action_light_on();
    //~ } 
    //~ else
      //~ return 6;
  //~ }      
  else
  {
    // unknown command
    return 2;
  }
  return 0;
}
