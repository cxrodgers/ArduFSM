// implementations for ir detector sampling functions
// supposed to be a drop-in replacement for mpr121

#include "ir_detector.h"
#include "Arduino.h"


int get_touched_channel(uint16_t touched, unsigned int i)
{
  return (touched & (1 << i)) >> i;
}

uint16_t pollTouchInputs()
{ /* Samples both ir pins and returns whether they are touched
  */

  int l_val = analogRead(__HWCONSTANTS_H_IR_L_PIN);
  int r_val = analogRead(__HWCONSTANTS_H_IR_R_PIN);
  uint16_t touched = 0;


  Serial.print("0 DBG ");
  Serial.print(l_val);
  Serial.print(" ");
  Serial.println(r_val);
  delay(500);
  
  if (l_val < __HWCONSTANTS_H_IR_L_THRESH)
    touched += 1;
  if (r_val < __HWCONSTANTS_H_IR_R_THRESH)
    touched += 2;
  
  return touched;
}  
