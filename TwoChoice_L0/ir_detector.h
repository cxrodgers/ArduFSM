// Header file for functions relating to sampling the IR detector
// This is supposed to be a drop-in replacement for mpr121.h

#ifndef __IR_DETECTOR_H_INCLUDED__
#define __IR_DETECTOR_H_INCLUDED__


#include "Arduino.h"
#include "hwconstants.h"

uint16_t pollTouchInputs(unsigned long time, bool debug=0);
int get_touched_channel(uint16_t touched, unsigned int i);

#define __IR_DETECTOR_H_BUFFER_SZ 20
#define __IR_DETECTOR_H_UPDATE_T 400
#endif