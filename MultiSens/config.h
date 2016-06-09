/* Last updated DDK 6/7/16
 *  
 * OVERVIEW:
 * This is a header file for config.cpp, which instantiates the device objects 
 * to be used in the current session of the ArduFSM protocol MultiSens. It also
 * defines a number of macros that specify hardware pins, step size, motor 
 * speeds, DC biases, etc., used in instantiating the device objects. 
 * 
 */
 
#ifndef CONFIG_MS_INCLUDED
#define CONFIG_MS_INCLUDED

#include "devices.h"                    
#define NUM_DEVICES 2

#define STPR1_PIN1 8
#define STPR1_PIN2 6      
#define ENBL1_PIN 7
#define HALL1_PIN 1
#define SPKR_PIN 13
#define SOLENOID_PIN 2
#define LICK_DETECTOR_PIN 10

#define NUM_STEPS 200
#define HALL1_THRESH 50
#define STPR1_SPEED 80
#define STPR1_CW -20
#define STPR1_CCW 20
#define HALL1_VAL 500   

Device ** config_hw();

#endif 
