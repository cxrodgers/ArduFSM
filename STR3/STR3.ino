/* Very simple protocol to test freezing problem.

Just creates a stepper object. Often freezes when trying to step it.
*/
//#include "chat.h"
//#include "States.h"
//~ #include "ArduFSM.h"
#include "Stepper.h"
//~ #include "Servo.h"
//~ #include "mpr121.h"
//~ #include <Wire.h>
#include "hwconstants.h"

//Stepper *stimStepper = 0;
//~ Servo servo;

Stepper stimStepper = Stepper(__HWCONSTANTS_H_NUMSTEPS, 
    PIN_STEPPER1, PIN_STEPPER2, PIN_STEPPER3, PIN_STEPPER4); 


void setup() {
  Serial.begin(115200);
   //~ stimStepper = new Stepper(__HWCONSTANTS_H_NUMSTEPS, 
      //~ PIN_STEPPER1, PIN_STEPPER2, PIN_STEPPER3, PIN_STEPPER4); 
  
}

void loop() {
  Serial.println("DBG stepping");
  delay(500);
  rotate(1);  
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
  stimStepper.step(n_steps);
Serial.println("DBG stepping2");
  // This delay doesn't seem necessary
  //delay(50);
  
Serial.println("DBG stepping3");
  digitalWrite(ENABLE_STEPPER, LOW);
  
  return 0;
}