#include "chat.h"


// This stuff is all here just because it is required by chat
bool flag_start_trial = 0;
int take_action(char *protocol_cmd, char *argument1, char *argument2);
int take_action(char *protocol_cmd, char *argument1, char *argument2) {
  return 0;
}

// Setup function
void setup() {
  unsigned long time = millis();
  
  Serial.begin(115200); // set the baud rate
  Serial.print(time);
  Serial.println(" DBG begin setup");
}

// Loop function
void loop() {
  unsigned long time = millis();
  int status = 666;
  
  status = communications(time);
}