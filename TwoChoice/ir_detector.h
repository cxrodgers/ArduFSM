// Header file for functions relating to sampling the IR detector
// This is supposed to be a drop-in replacement for mpr121.h

#ifndef __IR_DETECTOR_H_INCLUDED__
#define __IR_DETECTOR_H_INCLUDED__


#include "Arduino.h"
#include "hwconstants.h"

uint16_t pollTouchInputs(void);
int get_touched_channel(uint16_t touched, unsigned int i);

#endif