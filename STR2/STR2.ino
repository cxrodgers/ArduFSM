/* Very simple protocol to test freezing problem.

Just creates a stepper object. Often freezes when trying to step it.

-------------------
Saved reports: 9
Next report: 9
0: word-address=0x22A: byte-address=0x454, data=0x0
1: word-address=0x21B: byte-address=0x436, data=0x0
2: word-address=0x21B: byte-address=0x436, data=0x0
3: word-address=0x498: byte-address=0x930, data=0x0
4: word-address=0x21E: byte-address=0x43C, data=0x0
5: word-address=0x21E: byte-address=0x43C, data=0x0
6: word-address=0x498: byte-address=0x930, data=0x0
7: word-address=0x21B: byte-address=0x436, data=0x0
8: word-address=0x21B: byte-address=0x436, data=0x0

*/
#include "Stepper.h"
#include "ApplicationMonitor.h"

Watchdog::CApplicationMonitor ApplicationMonitor;

// hardware constants
#define ENABLE_STEPPER 12
#define PIN_STEPPER1 8
#define PIN_STEPPER2 9
#define PIN_STEPPER3 10
#define PIN_STEPPER4 11
#define __HWCONSTANTS_H_NUMSTEPS 200
#define __HWCONSTANTS_H_STP_POST_ENABLE_DELAY 100

//~ Stepper stimStepper(__HWCONSTANTS_H_NUMSTEPS, 
    //~ PIN_STEPPER1, PIN_STEPPER2, PIN_STEPPER3, PIN_STEPPER4); 
Stepper *stimStepper = 0;

void setup() {
  Serial.begin(115200);
  stimStepper = new Stepper(__HWCONSTANTS_H_NUMSTEPS, 
    PIN_STEPPER1, PIN_STEPPER2, PIN_STEPPER3, PIN_STEPPER4); 

  ApplicationMonitor.Dump(Serial);
  ApplicationMonitor.EnableWatchdog(Watchdog::CApplicationMonitor::Timeout_4s);
}

void loop() {
  ApplicationMonitor.IAmAlive();
  //ApplicationMonitor.SetData(g_nIterations++);
  
  Serial.println("DBG stepping");
  delay(500);
  rotate(1);  
}

int rotate(long n_steps)
{
  digitalWrite(ENABLE_STEPPER, HIGH);
  Serial.println("DBG stepping0");

  delay(__HWCONSTANTS_H_STP_POST_ENABLE_DELAY);
  Serial.println("DBG stepping1");

  // This is where the freeze usually happens
  stimStepper->step(n_steps);

  // never get here
  Serial.println("DBG stepping2");
  Serial.println("DBG steppinaweffffffffffffffffffffffffffffffffffffffffffffffffg3");

  digitalWrite(ENABLE_STEPPER, LOW);  
  return 0;
}