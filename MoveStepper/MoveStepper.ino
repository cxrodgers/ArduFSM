#include "Arduino.h"

// Copied from hwconstants.h and config.h
#define __HWCONSTANTS_H_STEP_ENABLE 7
#define __HWCONSTANTS_H_STEP_PIN 6
#define __HWCONSTANTS_H_STEP_DIR 8

#define __HWCONSTANTS_H_STEP_HALFDELAY_US 4000
#define __HWCONSTANTS_H_MICROSTEP 8


// This is the rotation function from TwoChoice
void rotate_one_step()
{ // Pulse the step pin, then delay the specified number of microseconds
  digitalWrite(__HWCONSTANTS_H_STEP_PIN, HIGH);
  delayMicroseconds(__HWCONSTANTS_H_STEP_HALFDELAY_US / 
    __HWCONSTANTS_H_MICROSTEP);
  digitalWrite(__HWCONSTANTS_H_STEP_PIN, LOW);
  delayMicroseconds(__HWCONSTANTS_H_STEP_HALFDELAY_US / 
    __HWCONSTANTS_H_MICROSTEP);  
}

void setup() {
  Serial.begin(115200);
  pinMode(__HWCONSTANTS_H_STEP_ENABLE, OUTPUT);
  pinMode(__HWCONSTANTS_H_STEP_PIN, OUTPUT);
  pinMode(__HWCONSTANTS_H_STEP_DIR, OUTPUT);

  digitalWrite(__HWCONSTANTS_H_STEP_ENABLE, LOW);
  
  rotate_one_step();
}


void loop() {
  //int sensor = 512;
  
  //~ for(int i=0; i < __HWCONSTANTS_H_MICROSTEP; i++) {
    //~ rotate_one_step();
  //~ }

  //sensor = analogRead(1);
  //Serial.println(sensor);
  
  delay(3000);
}