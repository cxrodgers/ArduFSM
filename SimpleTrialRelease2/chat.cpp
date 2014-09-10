#include "Arduino.h"
#include "chat.h"





//// Globals for receiving chats
String receive_buffer = "";
String receive_line = "";

String receive_chat()
{
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
    // This needs to take Windows newlines into account too
    Serial.print(receive_line.substring(0, receive_line.length()-1));
    Serial.println("");   
    return_value = receive_line;
    receive_line = "";
  }
  
  return return_value;
}




//// Begin TrialSpeak code.
//   This should probably be moved to its own file.
int handle_chat(String received_chat, TRIAL_PARAMS_TYPE &trial_params, bool &flag_start_next_trial)
{ /* Update the trial parameters with user requests 
  
  Returns 1 if cannot parse command
  */
  char *pch;
  char cmd_carr[cmd.length() + 1];
  char *strs[3];
  int n_strs = 0;
  String s;

  // Convert to array of strings
  if (cmd.length() <= 1)
  {
    return 1;
  }      
  cmd.toCharArray(cmd_carr, cmd.length() + 1);
  pch = strtok(cmd_carr, " ");
  while (pch != NULL)
  {
    strs[n_strs] = pch;
    n_strs++;
    pch = strtok(NULL, " ");
  }
  
  // Return if nothing
  if (n_strs == 0)
  {
    return 1;
  }
  
  //// Parse
  // First switch on first word
  if (strcmp(strs[0], "SET") == 0)
  {
    //// We're setting a variable. Switch on which variable
    if (n_strs != 3)
    {
      // syntax error
      return 3;
    }
    if (strcmp(strs[1], "ITI") == 0)
    {
      trial_params.inter_trial_interval = ((String) strs[2]).toInt();
    }
    else
    {
      // unknown variable
      return 4;
    }
  }  
  else if (strcmp(strs[0], "RELEASE_TRL") == 0)
  {
    if (n_strs 
  }
  
  else
  {
    // unimplemented command
    return 2;
  }
  
  return 0;
}   


int handle_chat(received_chat, flag_start_next_trial, trial_params)
{ /* Parse received_chat and set the flag or trial params as appropriate.
  */
  check_for_release_trial(received_chat, flag_start_next_trial);
  if (received_chat == String("RELEASE_TRL\n"))
  {
    flag_start_next_trial = 1;
  }
  int status = set_trial_params(trial_params, received_chat);
  
  // Error message
  if (status != 0)
  {
    Serial.println("DBG parse error");
  }
    Serial.println((String) "DBG cannot parse " + received_chat);
}


int check_for_release_trial(received_chat, bool &flag_start_next_trial)
{ /* Checks if the release trial command was received and sets flag if so */    
  if (received_chat == String("RELEASE_TRL\n"))
  {
    flag_start_next_trial = 1;
  }
  return 0;
}