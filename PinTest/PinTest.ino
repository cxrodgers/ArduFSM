#include "Arduino.h"

void setup()
{
  unsigned long time = millis();
  int status = 1;
  
  Serial.begin(115200);
  Serial.print(time);
  Serial.println("PinTest");

  
  pinMode(10, OUTPUT);    
  pinMode(11, OUTPUT);
  pinMode(12, OUTPUT);    
  pinMode(13, OUTPUT);
  
}

void loop()
{
    //~ Serial.println("Setting pin high");
    //~ digitalWrite(2, LOW);
    //~ digitalWrite(11, HIGH);
    
    //~ int val;
    //~ val = digitalRead(2);
    //~ Serial.println(val);
    //~ delay(1000);
  Serial.println("HIGH");
  digitalWrite(9, HIGH);
  digitalWrite(10, HIGH);
  digitalWrite(11, HIGH);
  digitalWrite(12, HIGH);
  digitalWrite(13, HIGH);
  delay(3000);
  Serial.println("LOW");
  digitalWrite(9, LOW);
  digitalWrite(10, LOW);
  digitalWrite(11, LOW);
  digitalWrite(12, LOW);
  digitalWrite(13, LOW);
  delay(3000);
}