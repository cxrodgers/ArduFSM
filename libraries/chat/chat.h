// Header file for chatting.
// Also includes some TrialSpeak stuff that is dependent on specific 
// trial protocol, so this should be changed.

#ifndef __CHAT_H_INCLUDED__
#define __CHAT_H_INCLUDED__

#include "Arduino.h"

// Chat defines
#define __CHAT_H_MAX_TOKENS 3
#define __CHAT_H_MAX_TOKEN_LEN 15
#define __CHAT_H_RECEIVE_BUFFER_SZ 100

//// Trial speak stuff. Should probably be moved to its own file.
#define __TRIAL_SPEAK_YES 3
#define __TRIAL_SPEAK_NO 2
#define __TRIAL_SPEAK_MUST_DEFINE 0

int communications(unsigned long time);
int handle_chat(char* received_chat,
  bool &flag_start_trial, char *protocol_cmd, char *argument1,
  char *argument2);
int safe_int_convert(char *string_data, long &variable);

//// General chat stuff
char* receive_chat();

#endif