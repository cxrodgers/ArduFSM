/* Simple protocol to test the "trial release" functionality. 

On each trial, the arduino does nothing except listen for chats and
waits to receive a "RELEASE_TRL" command. Upon this command, it terminates
the current trial and begins the next one.

This has only the three standard states defined in the ArduFSM library.
[*] wait_to_start_trial 
[*] trial_start
[*] inter_trial_interval

This simple protocol also serves as a template for more complex protocols.
Every ino file should define the following:
void user_setup1()
void user_setup2()
void user_every_loop()
State* user_trial_start()

Additionally, you can provide the following:
* States.h, States.cpp : additional states beyond the standard ones
* Actions.h, Actions.cpp : asynchronous actions
* Params.h, Params.cpp : parameters and results variables
*/
#include "chat.h"
#include "States.h"
#include "ArduFSM.h"

// Standared user_setup1() function, run before first communications.
// This simple protocol doesn't require anything here.
void user_setup1() {  
  Serial.print(millis());
  Serial.println(" DBG user_setup1");
}

// Standard user_setup1() function, run after first communications complete.
// This simple protocol doesn't require anything here.
void user_setup2() {  
  Serial.print(millis());
  Serial.println(" DBG user_setup2");
}

// Standard user_every_loop() function, run on every loop
void user_every_loop() {
  
}

// Standard user_trial_start() function, run at beginning of every trial
State* user_trial_start(unsigned long time) {
  Serial.print(time);
  Serial.println(" DBG uts");
  return state_finish_trial;
}