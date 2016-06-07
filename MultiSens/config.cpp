#include "config.h"

Device ** config_hw(){ 

  static myStepper myStp1( NUM_STEPS, STPR1_PIN1, STPR1_PIN1, ENBL1_PIN, HALL1_PIN, HALL1_THRESH, STPR1_SPEED, STPR1_CW, STPR1_CCW, HALL1_VAL );  
  static mySpeaker spkr1( SPKR_PIN );
  
  static Device * devPtrs[] = { &myStp1, &spkr1 };
  return devPtrs;
}

