/* A two-alternative choice behavior with left and right lick ports.

On each trial, the stepper is rotated to the correct stimulus position,
the servo is moved closed to the subject, and the response window begins
Correct responses are rewarded; incorrect punsihed with a timeout.
Then the next trial begins.

TODO
----
* figure out how to exchange touched, linServo, etc between states and here
* autogenerate Params.h
* diagnostics: which state it is in on each call (or subset of calls)

Boilerplate documentation for all protocols
---
Every ino file should define the following:
void user_setup1()
void user_setup2()
void user_every_loop()
State* user_trial_start()

*/
#include "chat.h"
#include "hwconstants.h"
#include "mpr121.h"
#include <Wire.h> // also for mpr121
#include <Servo.h>
#include <Stepper.h>
#include "States.h"
#include "ArduFSM.h"
#include "Arduino.h"
#include "Params.h"


//// Global variables. These are global because they are used in this
// file, and also in multiple different states.

// initial position of stim arm .. user must ensure this is correct
//~ long sticky_stepper_position = 0;

// Stepper. We won't assign till we know if it's 2pin or 4pin
//~ Stepper *stimStepper = 0;


// Standard user_setup1 function
// Sets pins as inputs/outputs
// Connects to MPR121 and servo
void user_setup1() {
  Serial.print(millis());
  Serial.println(" DBG begin user_setup1");

}

// Standard user_setup2() function, run after first communications complete.
// Sets up two-pin or four-pin stepper, sets thresholds for MPR121,
// moves servo to initial position.
void user_setup2() {
  Serial.print(millis());
  Serial.println(" DBG begin user_setup2");

}

// Standard user_every_loop() function, run on every loop
void user_every_loop(unsigned long time) {

}

// Standard user_trial_start() function, run at beginning of every trial
State* user_trial_start(unsigned long time) {
  // Update state timers
  static_cast<TimedState *>(state_error_timeout)->set_duration(
    param_values[tpidx_ERROR_TIMEOUT]);
  static_cast<TimedState *>(state_response_window)->set_duration(
    param_values[tpidx_RESP_WIN_DUR]);
  static_cast<TimedState *>(state_wait_for_servo_move)->set_duration(
    param_values[tpidx_SRV_TRAVEL_TIME]);
  static_cast<TimedState *>(state_post_reward_pause)->set_duration(
    param_values[tpidx_INTER_REWARD_INTERVAL]);
  
  return state_rotate_stepper1;
}
