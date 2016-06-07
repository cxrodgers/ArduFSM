#include "config_dummy.h"

Device ** config_hw(){ 
  static dummyStepper dmStpr1;
  static dummySpeaker dmSpkr1;
  
  static Device * devPtrs[] = { &dmStpr1, &dmSpkr1 };
  return devPtrs;
}

