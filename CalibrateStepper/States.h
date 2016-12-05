/* Header file for declaring rotation functions.

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


