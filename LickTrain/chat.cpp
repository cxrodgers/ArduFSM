#include "Arduino.h"
#include "chat.h"


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
    Serial.print("ACK ");
    
    // Strip the newline
    // This needs to take Windows newlines into account too
    Serial.print(receive_line.substring(0, receive_line.length()-1));
    Serial.println("");   
    return_value = receive_line;
    receive_line = "";
  }
  
  return return_value;
}