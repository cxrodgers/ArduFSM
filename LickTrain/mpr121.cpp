#include "Arduino.h"
#include "mpr121.h"
#include <Wire.h> # also for mpr121

int IRQ_LINE = -1;

/* Global variable `touched`.
The detector raises an interrupt whenever a change occurs. At any point
the value on each line can be read, though this can take ~200us or so,
much longer than checking the interrupt.

Use a global variable to latch the value of `touched` over loops. Only update
whenever the IRQ line is high. This way we know the current value even 
if no interrupt has occurred since the last loop.

Here is the incantation for extracting a specific bit:
touchStates[i] = (touched & (1 << i)) >> i;
*/
uint16_t touched = 0;


// subfunctions for MPR121 operation
uint16_t pollTouchInputs()
{ /* Update `touched` as necessary to match current lick state.
  `touched` is a global, persistent throughout the session.
  If the IRQ line is low, this means nothing has changed and this returns
  immediately.
  If the IRQ line is high, the new value is read into `touched`.
  */
  // Including this check increases speed by a huge amount, ~40x overall
  // Edge case: what if we've been continuously touching since last trial?
  // Then no interrupt and no detection.
  // So we should either latch the last-known value, or check that it is zero
  // before polling.
  if (checkInterrupt()) {
    return touched;
  }
  
  //read the touch state from the MPR121
  Wire.requestFrom(0x5A,2); 

  // Read the 16 bits (LSB=ch0)
  byte LSB = Wire.read();
  byte MSB = Wire.read();
  touched = ((MSB << 8) | LSB); //16bits that make up the touch states
  return touched;
}  

void mpr121_setup(int irq_line)
{
  // Save the pin for interrupts so that check_interrupts can use it
  IRQ_LINE = irq_line;
    
  set_register(0x5A, ELE_CFG, 0x00); 

  // Section A - Controls filtering when data is > baseline.
  set_register(0x5A, MHD_R, 0x01);
  set_register(0x5A, NHD_R, 0x01);
  set_register(0x5A, NCL_R, 0x00);
  set_register(0x5A, FDL_R, 0x00);

  // Section B - Controls filtering when data is < baseline.
  set_register(0x5A, MHD_F, 0x01);
  set_register(0x5A, NHD_F, 0x01);
  set_register(0x5A, NCL_F, 0xFF);
  set_register(0x5A, FDL_F, 0x02);

  // Section C - Sets touch and release thresholds for each electrode
  set_register(0x5A, ELE0_T, TOU_THRESH);
  set_register(0x5A, ELE0_R, REL_THRESH);

  set_register(0x5A, ELE1_T, TOU_THRESH);
  set_register(0x5A, ELE1_R, REL_THRESH);

  set_register(0x5A, ELE2_T, TOU_THRESH);
  set_register(0x5A, ELE2_R, REL_THRESH);

  set_register(0x5A, ELE3_T, TOU_THRESH);
  set_register(0x5A, ELE3_R, REL_THRESH);

  set_register(0x5A, ELE4_T, TOU_THRESH);
  set_register(0x5A, ELE4_R, REL_THRESH);

  set_register(0x5A, ELE5_T, TOU_THRESH);
  set_register(0x5A, ELE5_R, REL_THRESH);

  set_register(0x5A, ELE6_T, TOU_THRESH);
  set_register(0x5A, ELE6_R, REL_THRESH);

  set_register(0x5A, ELE7_T, TOU_THRESH);
  set_register(0x5A, ELE7_R, REL_THRESH);

  set_register(0x5A, ELE8_T, TOU_THRESH);
  set_register(0x5A, ELE8_R, REL_THRESH);

  set_register(0x5A, ELE9_T, TOU_THRESH);
  set_register(0x5A, ELE9_R, REL_THRESH);

  set_register(0x5A, ELE10_T, TOU_THRESH);
  set_register(0x5A, ELE10_R, REL_THRESH);

  set_register(0x5A, ELE11_T, TOU_THRESH);
  set_register(0x5A, ELE11_R, REL_THRESH);

  // Section D
  // Set the Filter Configuration
  // Set ESI2
  set_register(0x5A, FIL_CFG, 0x04);

  // Section E
  // Electrode Configuration
  // Set ELE_CFG to 0x00 to return to standby mode
  set_register(0x5A, ELE_CFG, 0x0C);  // Enables all 12 Electrodes


  // Section F
  // Enable Auto Config and auto Reconfig
  /*set_register(0x5A, ATO_CFG0, 0x0B);
   set_register(0x5A, ATO_CFGU, 0xC9);  // USL = (Vdd-0.7)/vdd*256 = 0xC9 @3.3V   set_register(0x5A, ATO_CFGL, 0x82);  // LSL = 0.65*USL = 0x82 @3.3V
   set_register(0x5A, ATO_CFGT, 0xB5);*/  // Target = 0.9*USL = 0xB5 @3.3V

  set_register(0x5A, ELE_CFG, 0x0C);

}

boolean checkInterrupt()
{
  return digitalRead(IRQ_LINE);
}

void set_register(int address, unsigned char r, unsigned char v)
{
  Wire.beginTransmission(address);
  Wire.write(r); //Wire.send(r);
  Wire.write(v); //Wire.send(v);
  Wire.endTransmission();
}