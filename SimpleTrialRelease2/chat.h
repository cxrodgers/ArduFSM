#include "Arduino.h"


//// Trial speak stuff. Should probably be moved to its own file.
// Trial params
// Characteristics of each trial. These can all be modified by the user.
// However, there is no guarantee that the newest value will be used until
// the current trial is released.
struct TRIAL_PARAMS_TYPE
{
  unsigned long inter_trial_interval = 3000;
};

// parsing user commands into parameter setting
int set_trial_params(TRIAL_PARAMS_TYPE &trial_params, String cmd);


//// General chat stuff
String receive_chat();
