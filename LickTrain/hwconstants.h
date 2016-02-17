#ifndef __HWCONSTANTS_H_INCLUDED__
#define __HWCONSTANTS_H_INCLUDED__

// Define all constants that are true for all rigs
// Rig-specific changes can be made by setting parameters in the usual way
// Otherwise we need different versions of the protocol


//// DIGITAL

// Two-pin mode
#define TWOPIN_ENABLE_STEPPER 7
#define TWOPIN_STEPPER_1 6
#define TWOPIN_STEPPER_2 8

// Four-pin mode
#define ENABLE_STEPPER 12
#define PIN_STEPPER1 8
#define PIN_STEPPER2 9
#define PIN_STEPPER3 10
#define PIN_STEPPER4 11

// Rewards
#define L_REWARD_VALVE 4
#define R_REWARD_VALVE 5
#define TOUCH_IRQ 2

// light
#define __HWCONSTANTS_H_HOUSE_LIGHT 3

// Servo
#define LINEAR_SERVO 13

//// ANALOG
#define __HWCONSTANTS_H_HALL 0

//// Misc
#define __HWCONSTANTS_H_NUMSTEPS 200
#define __HWCONSTANTS_H_STP_POST_ENABLE_DELAY 100

#endif