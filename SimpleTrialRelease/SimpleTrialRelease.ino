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
#include "Stepper.h"
//~ #include "Servo.h"
//~ #include "mpr121.h"
//~ #include <Wire.h>
#include "hwconstants.h"

Stepper *stimStepper = 0;
//~ Servo servo;


// Standard user_setup1() function, run before first communications.
// This simple protocol doesn't require anything here.
void user_setup1() {  
  Serial.print(millis());
  Serial.println(" DBG user_setup1");
}

// Standard user_setup2() function, run after first communications complete.
// This simple protocol doesn't require anything here.
void user_setup2() {  
  Serial.print(millis());
  Serial.println(" DBG user_setup2");
  
  
  stimStepper = new Stepper(__HWCONSTANTS_H_NUMSTEPS, 
      PIN_STEPPER1, PIN_STEPPER2, PIN_STEPPER3, PIN_STEPPER4);
  //~ servo.attach(LINEAR_SERVO);
  // thresholds for MPR121
  //~ mpr121_setup(TOUCH_IRQ, 6, 6);
}

// Standard user_every_loop() function, run on every loop
void user_every_loop(unsigned long time) {
  Serial.println("DBG stepping");
  delay(500);
  rotate(1);
}

// Standard user_trial_start() function, run at beginning of every trial
State* user_trial_start(unsigned long time) {
  // Update the length of the wait state
  static_cast<TimedState *>(state_wait)->set_duration(
    param_values[tpidx_ITI]);
  
  return state_wait;
}



int rotate(long n_steps)
{ /* Low-level rotation function 
  
  I think positive n_steps means CCW and negative n_steps means CW. It does
  on L2, at least.
  */

  digitalWrite(ENABLE_STEPPER, HIGH);
Serial.println("DBG stepping0");
  // Sometimes the stepper spins like crazy without a delay here
  delay(__HWCONSTANTS_H_STP_POST_ENABLE_DELAY);
  Serial.println("DBG stepping1");
  // BLOCKING CALL //
  // Replace this with more iterations of smaller steps
  stimStepper->step(n_steps);
Serial.println("DBG stepping2");
  // This delay doesn't seem necessary
  //delay(50);
  
Serial.println("DBG stepping3");
  digitalWrite(ENABLE_STEPPER, LOW);
  
  return 0;
}