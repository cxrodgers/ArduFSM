// Implementations of functions needed for chatting
// Also presently includes TrialSpeak stuff which should probably go
// to its own file.

#include "Arduino.h"
#include "chat.h"





//// Globals for receiving chats
// These need to persist across calls to receive_chat
String receive_buffer = "";
String receive_line = "";


//// Functions for receiving chats
String receive_chat()
{ /* Basic function to receive chats.
  
  Checks Serial.available
  Once a newline has been received, store it in `receive_line` and return it.
  Will also echo it as an ACK.
  Otherwise keep it in the buffer.
  */
  // If characters available, add to buffer
  int n_chars = Serial.available();
  char got = 'X';
  String return_value = "";
  
  for(int ichar = 0; ichar < n_chars; ichar++)
  {
    got = Serial.read();

    if (got == '\n')
    {
      // Add the newline
      receive_buffer += got;
      
      // Put buffer in line
      // Start buffer over
      receive_line = receive_buffer;
      receive_buffer = "";
      break;
    }
    else
    {
      receive_buffer += got;
    }
  }
  
  // If a line available, echo it
  if (receive_line.length() > 0)
  {
    Serial.print((String) millis() + " ACK ");
    
    // Strip the newline
    receive_line.trim();

    // Now print
    Serial.print(receive_line);
    Serial.println("");   
    
    // Store in return value and reset line to empty
    return_value = receive_line;
    receive_line = "";
  }
  
  return return_value;
}




//// Begin TrialSpeak code.
// This function is gummed up with specific trial protocol stuff.
int handle_chat(String received_chat, 
  bool &flag_start_next_trial, String &protocol_cmd, String &argument1,
  String &argument2)
{ /* Parses a received line and takes appropriate action.
  
  Currently the only command this can parse is RELEASE_TRL. Other general
  TrialSpeak commands should go here.

  If a protocol-specific command is received (e.g., "SET"), then 
  the following String variables are set:
    protocol_cmd, argument1, argument2
  This will be with the first word (command), and 2nd and 3rd words.
    
  Return values:
  0 - command parsed successfully
  1 - command contained no tokens or was empty
  2 - unimplemented command (first word)
  3 - syntax error: number of words did not match command
  */
  char *pch;
  char cmd_carr[received_chat.length() + 1];
  char *strs[3];
  int n_strs = 0;
  String s;

  // Return if nothing. Typically the calling code already protects this.
  if (received_chat.length() <= 1)
  {
    return 1;
  }      
  
  // Parsing into space-separated tokens
  received_chat.toCharArray(cmd_carr, received_chat.length() + 1);
  pch = strtok(cmd_carr, " ");
  while (pch != NULL)
  {
    strs[n_strs] = pch;
    n_strs++;
    pch = strtok(NULL, " ");
  }
  
  // Return if nothing. Typically the calling code has already trimmed and
  // checked for empty, so this shouldn't happen.
  if (n_strs == 0)
  {
    return 1;
  }
  
  //// Parse according to TrialSpeak convention.
  // First switch on first word, then on number of strings, then potentially
  // on subsequent words.
  // Figure out how to offload the protocol-specific parameters to
  // something in the protocol file.
  
  //// Setting a variable
  if (strcmp(strs[0], "SET") == 0)
  {
    if (n_strs != 3)
    {
      // syntax error
      return 3;
    }
    protocol_cmd = (String) "SET";
    argument1 = (String) strs[1];
    argument2 = (String) strs[2];
    return 0;
  }  
  
  //// Releasing a trial
  else if (strcmp(strs[0], "RELEASE_TRL") == 0)
  {
    if (n_strs != 1)
    {
      // syntax error
      return 3;
    }
    else
    {
      flag_start_next_trial = 1;
    }
  }
  
  //// Unimplemented command
  else
  {
    return 2;
  }
  
  return 0;
}   


// Alternate implementations graveyard
//// Basic TrialSpeak stuff
//~ int handle_chat(received_chat, flag_start_next_trial, trial_params)
//~ { /* Parse received_chat and set the flag or trial params as appropriate.
  //~ */
  //~ check_for_release_trial(received_chat, flag_start_next_trial);
  //~ if (received_chat == String("RELEASE_TRL\n"))
  //~ {
    //~ flag_start_next_trial = 1;
  //~ }
  //~ int status = set_trial_params(trial_params, received_chat);
  
  //~ // Error message
  //~ if (status != 0)
  //~ {
    //~ Serial.println("DBG parse error");
  //~ }
    //~ Serial.println((String) "DBG cannot parse " + received_chat);
//~ }


//~ int check_for_release_trial(received_chat, bool &flag_start_next_trial)
//~ { /* Checks if the release trial command was received and sets flag if so */    
  //~ if (received_chat == String("RELEASE_TRL\n"))
  //~ {
    //~ flag_start_next_trial = 1;
  //~ }
  //~ return 0;
//~ }