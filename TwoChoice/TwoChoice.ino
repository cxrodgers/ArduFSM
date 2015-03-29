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


//// Global variables, to be passed around between states
// touched monitor
uint16_t sticky_touched = 0;

// initial position of stim arm .. user must ensure this is correct
long sticky_stepper_position = 0;

// Servo
Servo linServo;

// Stepper
// We won't assign till we know if it's 2pin or 4pin
Stepper *stimStepper = 0;


// Standard user_setup1 function
// Sets pins as inputs/outputs
// Connects to MPR121 and servo
void user_setup1() {
  Serial.print(millis());
  Serial.println(" DBG begin user_setup1");

  // MPR121 touch sensor setup
  pinMode(TOUCH_IRQ, INPUT);
  digitalWrite(TOUCH_IRQ, HIGH); //enable pullup resistor
  Wire.begin();
  
  // output pins
  pinMode(L_REWARD_VALVE, OUTPUT);
  pinMode(R_REWARD_VALVE, OUTPUT);
  pinMode(__HWCONSTANTS_H_HOUSE_LIGHT, OUTPUT);
  
  // initialize the house light to ON
  digitalWrite(__HWCONSTANTS_H_HOUSE_LIGHT, HIGH);
  
  // random number seed
  randomSeed(analogRead(3));

  // attach servo
  linServo.attach(LINEAR_SERVO);  
}

// Standard user_setup2() function, run after first communications complete.
// Sets up two-pin or four-pin stepper, sets thresholds for MPR121,
// moves servo to initial position.
void user_setup2() {
  // Set up the stepper according to two-pin or four-pin mode
  if (param_values[tpidx_2PSTP] == __TRIAL_SPEAK_YES)
  { // Two-pin mode
    pinMode(TWOPIN_ENABLE_STEPPER, OUTPUT);
    pinMode(TWOPIN_STEPPER_1, OUTPUT);
    pinMode(TWOPIN_STEPPER_2, OUTPUT);
    
    // Make sure it's off    
    digitalWrite(TWOPIN_ENABLE_STEPPER, LOW); 
    
    // Initialize
    stimStepper = new Stepper(__HWCONSTANTS_H_NUMSTEPS, 
      TWOPIN_STEPPER_1, TWOPIN_STEPPER_2);
  }
  else
  { // Four-pin mode
    pinMode(ENABLE_STEPPER, OUTPUT);
    pinMode(PIN_STEPPER1, OUTPUT);
    pinMode(PIN_STEPPER2, OUTPUT);
    pinMode(PIN_STEPPER3, OUTPUT);
    pinMode(PIN_STEPPER4, OUTPUT);
    digitalWrite(ENABLE_STEPPER, LOW); // # Make sure it's off
    
    stimStepper = new Stepper(__HWCONSTANTS_H_NUMSTEPS, 
      PIN_STEPPER1, PIN_STEPPER2, PIN_STEPPER3, PIN_STEPPER4);
  }
  
  // thresholds for MPR121
  mpr121_setup(TOUCH_IRQ, param_values[tpidx_TOU_THRESH], 
    param_values[tpidx_REL_THRESH]);

  // Set the speed of the stepper
  stimStepper->setSpeed(param_values[tpidx_STEP_SPEED]);
  
  // initial position of the stepper
  sticky_stepper_position = param_values[tpidx_STEP_INITIAL_POS];
  
  // linear servo setup
  linServo.write(param_values[tpidx_SRV_FAR]);
  delay(param_values[tpidx_SERVO_SETUP_T]);
}

// Standard user_every_loop() function, run on every loop
void user_every_loop(unsigned long time) {
  // Poll touch inputs
  uint16_t touched = 0;
  touched = pollTouchInputs();
  
  // announce sticky
  if (touched != sticky_touched)
  {
    Serial.print(time);
    Serial.print(" TCH ");
    Serial.println(touched);
    sticky_touched = touched;
  }   
}

// Standard user_trial_start() function, run at beginning of every trial
// Probably want to update state timers with params_values here
State* user_trial_start(unsigned long time) {
  return state_rotate_stepper1;
}
