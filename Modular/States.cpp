
#include "States.h"
#include "Arduino.h"
#include "hwconstants.h"


// include this one just to get __TRIAL_SPEAK_YES
#include "chat.h"


extern STATE_TYPE next_state;
extern bool flag_start_trial;

// These should go into some kind of Protocol.h or something
char const* param_abbrevs[N_TRIAL_PARAMS] = {
  "LIGHTON_DUR", "LIGHTOFF_DUR",
  };
long param_values[N_TRIAL_PARAMS] = {
  1000, 1000,
  };

bool param_report_ET[N_TRIAL_PARAMS] = {
  1, 1,
};


static StateLightOn state_light_on(param_values[tpidx_LIGHTON_DUR]);
static StateLightOff state_light_off(param_values[tpidx_LIGHTOFF_DUR]);


void stateDependentOperations(STATE_TYPE current_state, unsigned long time) {
    switch(current_state) {
      case LIGHT_ON:
        state_light_on.run(time);
        break;
      case LIGHT_OFF:
        state_light_off.run(time);
        break;
    };
};

//Definitions for TimedState subclasses
void StateLightOn::s_setup()
{
//  Serial.println(duration);
  duration = param_values[tpidx_LIGHTON_DUR];
  digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, HIGH); 

};


void StateLightOn::s_finish()
{
  next_state = LIGHT_OFF;
};

void StateLightOff::s_setup()
{  
  duration = param_values[tpidx_LIGHTOFF_DUR];
  digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, LOW); 
//  Serial.println(duration);
};



void StateLightOff::s_finish()
{
  next_state = LIGHT_ON;
};






