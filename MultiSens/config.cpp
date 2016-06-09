/* Last updated DDK 6/7/16
 * 
 * OVERVIEW:
 * This file contains instantiations of the device objects to be used on the current 
 * session of the ArduFSM protocol MultiSens. These objects manage the behavior
 * of devices like stepper motors, speakers, etc. For full documentation of 
 * these device classes, see the README.md for the devices library. 
 * 
 * This file also places the device objects in an array and returns the array
 * to States.cpp, precluding the need to adjust hardware parameters in States.cpp
 * from experiment to experiment.
 */

#include "config.h"

Device ** config_hw(){ 

  static myStepper myStp1( NUM_STEPS, STPR1_PIN1, STPR1_PIN1, ENBL1_PIN, HALL1_PIN, HALL1_THRESH, STPR1_SPEED, STPR1_CW, STPR1_CCW, HALL1_VAL );  
  static mySpeaker spkr1( SPKR_PIN );
  
  static Device * devPtrs[] = { &myStp1, &spkr1 };
  return devPtrs;
}

