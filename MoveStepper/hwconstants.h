// #define macros for protocol constants, like pin numbers
// rig-specific macros are defined in the auto-generated and included config.h

#ifndef __HWCONSTANTS_H_INCLUDED__
#define __HWCONSTANTS_H_INCLUDED__

#include "config.h"


//// DIGITAL
// Stepper control

// This is only for stepper driver
#ifdef __HWCONSTANTS_H_USE_STEPPER_DRIVER
#define __HWCONSTANTS_H_STEP_ENABLE 7
#define __HWCONSTANTS_H_STEP_PIN 6
#define __HWCONSTANTS_H_STEP_DIR 8
#endif

// This is only for H-bridge
#ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
#define TWOPIN_ENABLE_STEPPER 7
#define TWOPIN_STEPPER_1 6
#define TWOPIN_STEPPER_2 8
#endif

// Rewards
#define L_REWARD_VALVE 5
#define R_REWARD_VALVE 4
#define TOUCH_IRQ 2

// light
#define __HWCONSTANTS_H_HOUSE_LIGHT 3
#define __HWCONSTANTS_H_BACK_LIGHT 12

// Opto
#define __HWCONSTANTS_H_OPTO 10

// Servo
#define LINEAR_SERVO 13

//// ANALOG
#define __HWCONSTANTS_H_HALL1 1
#define __HWCONSTANTS_H_HALL2 0

#define __HWCONSTANTS_H_IR_L_PIN 2
#define __HWCONSTANTS_H_IR_R_PIN 3

#define __HWCONSTANTS_H_HALL_THRESH 50

//// Misc
#define __HWCONSTANTS_H_NUMSTEPS 200


#ifdef __HWCONSTANTS_H_USE_STEPPER_DRIVER
// This is only for stepper driver
// standard is 30 rpm, or 2s per rotation, or 10ms per step
// The half delay is 5000 us per step
// Will get bugs if this value is more than 16383
// With eg 1/4 stepping, this delay is 1/4 as long
#define __HWCONSTANTS_H_STEP_HALFDELAY_US 4000
#endif


#ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
// This is only for H-bridge
#define __HWCONSTANTS_H_STP_POST_ENABLE_DELAY 100
#endif


#define __HWCONSTANTS_H_SENSOR_HISTORY_SZ 10

#endif // #ifndef __HWCONSTANTS_H_INCLUDED__