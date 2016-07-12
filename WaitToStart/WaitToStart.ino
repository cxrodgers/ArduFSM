/* Simple protocol that receives parameters and a signal to start running.

This protocol is intended to demonstrate the following functionality:
* Receives parameters from a Python script (LIGHTON and LIGHTOFF)
* Waits for a signal before finishing setup() and entering loop()
The signal is the string "TRL_RELEASED" sent over the serial port.

Once loop() is entered, a digital input is raised for LIGHTON milliseconds
and lowered for LIGHTOFF milliseconds, to demonstrate that the parameter
was set correctly.
*/
#include "chat.h"
#include "hwconstants.h"

// This defines the number and order of the parameters
#define N_TRIAL_PARAMS 2
#define tpidx_LIGHTON 0 // first parameter
#define tpidx_LIGHTOFF 1 // second parameter

// These are the names of the parameters
char const* param_abbrevs[N_TRIAL_PARAMS] = {
  "LIGHTON", "LIGHTOFF",
  };

// This array stores the values of the parameters
// We start with some simple defaults
long param_values[N_TRIAL_PARAMS] = {
  100, 200,
  };

// flag to remember whether we've received the start signal
bool flag_start_trial = 0;

//// Declarations
int take_action(char *protocol_cmd, char *argument1, char *argument2);

//// Setup function
void setup()
{
  unsigned long time = millis();
  int status = 1;
  
  Serial.begin(115200);
  Serial.print(time);
  Serial.println(" DBG begin setup");

  //// Begin user protocol code
  // output pins
  pinMode(__HWCONSTANTS_H_HOUSE_LIGHT, OUTPUT);
  
  // initialize the house light to ON
  digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, HIGH);
  
  //// Run communications until we've received all setup info
  while (!flag_start_trial) {
    // Receive input from computer
    // If TRL_RELEASED is sent from computer, then this function
    // will set flag_start_trial to True
    status = communications(time);
    
    // communications returns non-zero value if some error occurred
    if (status != 0)
    {
      Serial.println("comm error in setup");
      delay(1000);
    }
  }
  
  digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, HIGH);
  Serial.print(millis());
  Serial.println(" ending setup()");  
}



//// Loop function
void loop()
{
  // alternate house light state based on designated durations
  Serial.print(millis());
  Serial.println(" flashing houselight");
  digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, HIGH);
  delay(param_values[tpidx_LIGHTON]);
  digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, LOW);
  delay(param_values[tpidx_LIGHTOFF]);
}

//// Helper functions for setting parameters
// Take protocol action based on user command (ie, setting variable)
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

