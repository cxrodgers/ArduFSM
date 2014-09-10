// Header file for chatting.
// Also includes some TrialSpeak stuff that is dependent on specific 
// trial protocol, so this should be changed.

#include "Arduino.h"


//// Trial speak stuff. Should probably be moved to its own file.


// parsing user commands into parameter setting
int handle_chat(String received_chat,
  bool &flag_start_next_trial, String &protocol_cmd, String &argument1,
  String &argument2);

//// General chat stuff
String receive_chat();
