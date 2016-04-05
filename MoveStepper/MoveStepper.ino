#include <Stepper.h>
#include "Arduino.h"

void setup() {
  Serial.begin(115200);
}


void loop() {
  int sensor = 512;
  
  sensor = analogRead(1);
  Serial.println(sensor);
  delay(100);
  
}