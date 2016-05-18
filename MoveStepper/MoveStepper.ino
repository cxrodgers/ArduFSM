#include <Stepper.h>
#include "Arduino.h"

Stepper stepper(200, 6, 8);

void setup() {
  Serial.begin(115200);
  pinMode(6, OUTPUT);
  pinMode(7, OUTPUT);
  pinMode(8, OUTPUT);
  
  stepper.setSpeed(30);
}


void loop() {
  int sensor = 512;
  
  digitalWrite(7, HIGH);
  delay(100);
  stepper.step(1);
  delay(100);
  digitalWrite(7, LOW);
  sensor = analogRead(1);
  Serial.println(sensor);
  delay(100);
}