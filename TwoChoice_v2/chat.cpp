// Implementations of functions needed for chatting
// Also presently includes TrialSpeak stuff which should probably go
// to its own file.

#include "Arduino.h"
#include "chat.h"



extern bool flag_start_trial;
extern int take_action(String protocol_cmd, String argument1, String argument2);

//// Globals for receiving chats
// These need to persist across calls to receive_chat
String receive_buffer = "";
String receive_line = "";

// Debugging announcements
unsigned long speak_at = 1000;
unsigned long interval = 1000;

// Output ring buffer
// Errors if this is more than 200
// And even if it is only 200 it starts acting weird
#define SZ_OUTPUT_BUFFER 200
#define OUTPUT_BUFFER_CHUNK 50
char output_buffer[SZ_OUTPUT_BUFFER];
int output_buffer_r = 0;
int output_buffer_w = 0;


int buffered_write(String s)
{
  // put string into buffer
  for(int ichar=0; ichar<s.length(); ichar++)
  {
    // Write each character into the buffer
    output_buffer[output_buffer_w] = s[ichar];
    
    // Increment write pointer  
    //~ Serial.println((String) output_buffer_w);
    output_buffer_w++;
    if (output_buffer_w >= SZ_OUTPUT_BUFFER)
    {
      output_buffer_w = 0;
    }
    
    // Error check
    if (output_buffer_w == output_buffer_r)
    {
      // r should always be lagging w immediately after a write.
      Serial.println("ERROR OUTPUT BUFFER OVERRUN");
    }
  }
}

int drain_output_buffer()
{
  // Write out at most OUTPUT_BUFFER_CHUNK characters
  // Ideally, we would also break this loop if the Serial.print buffer is full
  for(int ichar=0; ichar<OUTPUT_BUFFER_CHUNK; ichar++)
  {
    // Stop if there is no more to read
    if (output_buffer_r == output_buffer_w)
    {
      break;
    }
    
    // Read a character from buffer and print it
    Serial.print(output_buffer[output_buffer_r]);
    
    // Increment read pointer
    output_buffer_r++;
    if (output_buffer_r >= SZ_OUTPUT_BUFFER)
    {
      output_buffer_r = 0;
    }    
  }
}


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
int communications(unsigned long time)
{ /* Run the chat receiving and debug announcing stuff, independent of
    any state machine or user protocol stuff.
  
    Announces time, as necessary.
    Receives any chat and handles it, including calling take_action.
  */
  // comm variables
  String received_chat;
  String protocol_cmd = (String) "";
  String argument1 = (String) "";
  String argument2 = (String) "";
  int status = 1;
  
  
  //// Perform actions that occur on every call, independent of state
  // Announce the time
  if (time >= speak_at)
  {
    Serial.println((String) time + " DBG");
    speak_at += interval;
  }

  //// Drain the buffer
  //drain_output_buffer();
  
  //// Receive and deal with chat
  received_chat = receive_chat();
  if (received_chat.length() > 0)
  {
    // Attempt to parse
    status = handle_chat(received_chat, flag_start_trial,
        protocol_cmd, argument1, argument2);
    if (status != 0)
    {
      // Parse/syntax error
      Serial.println((String) time + " DBG RC_ERR " + (String) status);
    }
    else if (protocol_cmd.length() > 0)
    {
      // Protocol action required
      status = take_action(protocol_cmd, argument1, argument2);
      
      if (status != 0)
      {
        // Parse/syntax error
        Serial.println((String) time + " DBG TA_ERR " + (String) status);
      }
    }
  }
  
  return 0;
}

int handle_chat(String received_chat, 
  bool &flag_start_trial, String &protocol_cmd, String &argument1,
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
      flag_start_trial = 1;
    }
  }
  
  //// Unimplemented command
  else
  {
    return 2;
  }
  
  return 0;
}   

