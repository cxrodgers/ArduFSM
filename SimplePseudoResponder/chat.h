// Header file for chatting.
// Also includes some TrialSpeak stuff that is dependent on specific 
// trial protocol, so this should be changed.

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
int handle_chat(String received_chat, TRIAL_PARAMS_TYPE &trial_params, 
  bool &flag_start_next_trial, String &protocol_cmd, String &argument1,
  String &argument2);

//// General chat stuff
String receive_chat();
