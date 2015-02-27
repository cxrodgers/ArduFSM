// Implementations of functions needed for chatting
// Also presently includes TrialSpeak stuff which should probably go
// to its own file.

#include "Arduino.h"
#include "chat.h"



extern bool flag_start_trial;
extern int take_action(char *protocol_cmd, char *argument1, char *argument2);

//// Globals for receiving chats
// These need to persist across calls to receive_chat
char receive_buffer[__CHAT_H_RECEIVE_BUFFER_SZ] = "";
char receive_line[__CHAT_H_RECEIVE_BUFFER_SZ] = "";

// Debugging announcements
unsigned long speak_at = 1000;
unsigned long interval = 1000;



//// Functions for receiving chats
char* receive_chat()
{ /* Basic function to receive chats.
  
  Checks Serial.available
  Once a newline has been received, store it in `receive_line` and return it.
  Will also echo it as an ACK.
  Otherwise keep it in the buffer.
  */
  // If characters available, add to buffer
  int n_chars = Serial.available();
  char got = 'X';
  char return_value[__CHAT_H_RECEIVE_BUFFER_SZ] = "";
  
  for(int ichar = 0; ichar < n_chars; ichar++)
  {
    // get a character
    got = Serial.read();
    
    // error if overfow
    if (strlen(receive_buffer) >= __CHAT_H_RECEIVE_BUFFER_SZ - 1) {
      if (got != '\n') {
        Serial.println("ERR truncating buf overflow");
        got = '\n';
        
        // Should also empty the buffer or the next line will be garbage
      }
    }
    
    // add the character and a \0
    // latter is not necessary if we fill with \0 after every line
    receive_buffer[strlen(receive_buffer)] = got;
    receive_buffer[strlen(receive_buffer) + 1] = '\0';    
    
    // Check if this is end of line
    if (got == '\n')
    {
      // Put buffer in line
      strncpy(receive_line, receive_buffer, __CHAT_H_RECEIVE_BUFFER_SZ);
    
      // Start buffer over
      // Are we sure this fills with \0?
      strncpy(receive_buffer, "", __CHAT_H_RECEIVE_BUFFER_SZ);
      break;
    }
  }
  
  // If a line available, echo it
  if (strlen(receive_line) > 0)
  {
    // Print the ACK
    Serial.print(millis());
    Serial.print(" ACK ");
    Serial.print(receive_line); // still ends with \n
    
    // Store in return value and reset line to empty
    strncpy(return_value, receive_line, __CHAT_H_RECEIVE_BUFFER_SZ);
    strncpy(receive_line, "", __CHAT_H_RECEIVE_BUFFER_SZ);
  }
  
  return return_value;
}




//// Begin TrialSpeak code.
int communications(unsigned long time)
{ /* Run the chat receiving and debug announcing stuff, independent of
    any state machine or user protocol stuff.
  
    Announces time, as necessary.
    Receives any chat and handles it, including calling take_action.
  */
  // comm variables
  char* received_chat;
  char protocol_cmd[__CHAT_H_MAX_TOKEN_LEN] = "";
  char argument1[__CHAT_H_MAX_TOKEN_LEN] = "";
  char argument2[__CHAT_H_MAX_TOKEN_LEN] = "";
  int status = 1;
  
  
  //// Perform actions that occur on every call, independent of state
  // Announce the time
  if (time >= speak_at)
  {
    Serial.print(time);
    Serial.println(" DBG");
    speak_at += interval;
  }

  
  //// Receive and deal with chat
  received_chat = receive_chat();
  if (strlen(received_chat) > 0)
  {
    // Attempt to parse
    status = handle_chat(received_chat, flag_start_trial,
        protocol_cmd, argument1, argument2);
    if (status != 0)
    {
      // Parse/syntax error
      Serial.print(time);
      Serial.print(" DBG RC_ERR ");
      Serial.println(status);
    }
    //else if (protocol_cmd.length() > 0)
    else if (strlen(protocol_cmd) > 0)
    {
      // Protocol action required
      status = take_action(protocol_cmd, argument1, argument2);
      
      if (status != 0)
      {
        // Parse/syntax error
        Serial.print(time);
        Serial.print(" DBG TA_ERR ");
        Serial.println(status);
      }
    }
  }
  
  return 0;
}

int handle_chat(char* received_chat, 
  bool &flag_start_trial, char *protocol_cmd, char *argument1,
  char *argument2)
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
  4 - too many tokens
  */
  char *pch;
  char *strs[__CHAT_H_MAX_TOKENS];
  int n_strs = 0;

  // Return if nothing. Typically the calling code already protects this.
  if (strlen(received_chat) <= 1)
  {
    return 1;
  }      
  
  //// Parsing into space-separated tokens
  // split by spaces
  pch = strtok(received_chat, " \r\n");
  while (pch != NULL)
  {
    // Error if too many tokens received
    if (n_strs >= __CHAT_H_MAX_TOKENS) {
      return 4;
    }

    // Skip zero-length token, ie, between \r and \n
    if (strlen(pch) == 0) {
      continue;
    }
    
    // Otherwise store the token char array and continue
    strs[n_strs] = pch;
    n_strs++;
    pch = strtok(NULL, " \r\n");
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
  //// Setting a variable
  if (strncmp(strs[0], "SET\0", 4) == 0)
  {
    if (n_strs != 3)
    {
      // syntax error
      return 3;
    }
    strcpy(protocol_cmd, "SET");
    strncpy(argument1, strs[1], __CHAT_H_MAX_TOKEN_LEN);
    strncpy(argument2, strs[2], __CHAT_H_MAX_TOKEN_LEN);

    return 0;
  }  
  
  //// Releasing a trial
  else if (strncmp(strs[0], "RELEASE_TRL\0", 12) == 0)
  {
    if (n_strs != 1)
    {
      // syntax error
      return 3;
    }
    else
    {
      flag_start_trial = 1;
    }
  }
  
  //// User-defined command
  else if (strncmp(strs[0], "ACT\0", 4) == 0)
  {
    //protocol_cmd = (String) "ACT";
    strcpy(protocol_cmd, "ACT");
    
    // Parse 1 or 2 arguments
    if (n_strs == 2)
    {
      strncpy(argument1, strs[1], __CHAT_H_MAX_TOKEN_LEN);
      strcpy(argument2, "");
    }
    else if (n_strs == 3)
    {
      strncpy(argument1, strs[1], __CHAT_H_MAX_TOKEN_LEN);
      strncpy(argument2, strs[2], __CHAT_H_MAX_TOKEN_LEN);
    }
    else
    {
      // syntax error
      return 3;
    }
    
    // On return, user code will be executed
    return 0;
  }
  
  //// Unimplemented command
  else
  {
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