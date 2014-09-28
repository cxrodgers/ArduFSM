// Header file for chatting.
// Also includes some TrialSpeak stuff that is dependent on specific 
// trial protocol, so this should be changed.

#ifndef __CHAT_H_INCLUDED__
#define __CHAT_H_INCLUDED__

#include "Arduino.h"



//// Trial speak stuff. Should probably be moved to its own file.
int communications(unsigned long time);
int handle_chat(String received_chat,
  bool &flag_start_trial, String &protocol_cmd, String &argument1,
  String &argument2);

//// General chat stuff
String receive_chat();

#endif