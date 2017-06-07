// #define macros for protocol constants, like pin numbers
// rig-specific macros are defined in the auto-generated and included config.h

#ifndef __HWCONSTANTS_H_INCLUDED__
#define __HWCONSTANTS_H_INCLUDED__


#include "config.h"


//// DIGITAL

// Two-pin mode
#define TWOPIN_ENABLE_STEPPER 7
#define TWOPIN_STEPPER_1 6
#define TWOPIN_STEPPER_2 8

// Rewards
#define L_REWARD_VALVE 5
#define R_REWARD_VALVE 4
#define TOUCH_IRQ 2

// light
#define __HWCONSTANTS_H_HOUSE_LIGHT 3
#define __HWCONSTANTS_H_BACK_LIGHT 12

// Servo
#define LINEAR_SERVO 13

//// ANALOG
#define __HWCONSTANTS_H_HALL 1

#define __HWCONSTANTS_H_IR_L_PIN 0
#define __HWCONSTANTS_H_IR_R_PIN 2

//// Misc
#define __HWCONSTANTS_H_NUMSTEPS 200
#define __HWCONSTANTS_H_STP_POST_ENABLE_DELAY 100

#endif