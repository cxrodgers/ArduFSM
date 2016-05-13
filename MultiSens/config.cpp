#include "config.h"

Device ** config_hw(){ 
  static dummyStepper dmStpr1;
  static dummySpeaker dmSpkr1;
  //dummySpeaker dmSpkr;\

  /*
  const int NUM_STEPS = 200;
  const int STPR1_PIN1 = 8;
  const int STPR1_PIN2 = 6;      
  const int ENBL1_PIN = 7;
  const int HALL1_PIN = 1;
  const int HALL1_THRESH = 50;
  const int STPR1_SPEED = 80;
  const int STPR1_CW = -20;
  const int STPR1_CCW = 20;
  const int HALL1_VAL = 500;   
  */         
  static myStepper myStp1( NUM_STEPS, STPR1_PIN1, STPR1_PIN1, ENBL1_PIN, HALL1_PIN, HALL1_THRESH, STPR1_SPEED, STPR1_CW, STPR1_CCW, HALL1_VAL );
  
  static mySpeaker spkr1( SPKR_PIN );
  
  //static Device * devPtrs[] = { &dmStpr1, &dmSpkr1, &myStp1 };
  static Device * devPtrs[] = { &dmStpr1, &dmSpkr1 };
  return devPtrs;
}

