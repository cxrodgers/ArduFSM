
#include "States.h"
#include "Arduino.h"
#include "hwconstants.h"


// include this one just to get __TRIAL_SPEAK_YES
#include "chat.h"


// These should go into some kind of Protocol.h or something
char const* param_abbrevs[N_TRIAL_PARAMS] = {
  "LIGHTON", "LIGHTOFF",
  };
long param_values[N_TRIAL_PARAMS] = {
  1, 2,
  };

