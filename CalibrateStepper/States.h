/* Header file for declaring protocol-specific states.
This implements a two-alternative choice task with two lick ports.

Defines the following
* tpidx_ macros ... these allow you to index into trial_params
* tridx_ macros ... same, but for trial results
* the STATE_TYPE enum, which defines all possible states
* declarations for state functions and state objects, especially those derived
  from TimedState.

To define a new state, you should declare it here and put its implementation
into States.cpp.
*/


#include "hwconstants.h"
#include <Servo.h>



#define N_TRIAL_PARAMS 4
#define tpidx_SRV_FAR 0 // init-usually
#define tpidx_SERVO_SETUP_T 1 // init-only
#define tpidx_STEP_SPEED 2 // init-only
#define tpidx_STEP_INITIAL_POS 3 // init-only



// Declare utility functions
int rotate(long n_steps);
int rotate_to_sensor(int step_size, bool positive_peak, long set_position,
  int hall_sensor_id);
int rotate_to_sensor2();
int findStepperPeak();
int steps_to_max(int a[], int size);

#ifdef __HWCONSTANTS_H_USE_STEPPER_DRIVER
void rotate_one_step();
#endif


