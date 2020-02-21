// A simple standalone sketch to communicate with Python
// This is just a test of the receive_chat() function in the chat library
// But it doesn't require anything other than this script

// Define the buffer size
#define __CHAT_H_RECEIVE_BUFFER_SZ 100

//// Globals for receiving chats
// These need to persist across calls to receive_chat
char receive_buffer[__CHAT_H_RECEIVE_BUFFER_SZ] = "";
char receive_line[__CHAT_H_RECEIVE_BUFFER_SZ] = "";


void receive_chat(char* received_chat)
{ /* Basic function to receive chats.
  
  Checks Serial.available
  Once a newline has been received, store it in `receive_line` and return it.
  Will also echo it as an ACK.
  Otherwise keep it in the buffer.
  */
  // If characters available, add to buffer
  int n_chars = Serial.available();
  char got = 'X';
  
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
    
    // Store in received_chat and reset line to empty
    strncpy(received_chat, receive_line, __CHAT_H_RECEIVE_BUFFER_SZ);
    strncpy(receive_line, "", __CHAT_H_RECEIVE_BUFFER_SZ);
  }
}


// Setup function
void setup() {
  Serial.begin(115200); // set the baud rate
  Serial.println("Ready"); // print "Ready" once
}

// Loop function
void loop() {
  // define a variable to contain the received chat
  char received_chat[__CHAT_H_RECEIVE_BUFFER_SZ] = "";
  
  // receive a chat
  receive_chat(received_chat);
  
  // do stuff with it
  
  delay(500);
}