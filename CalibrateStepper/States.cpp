/* Implementation file for declaring protocol-specific states.
This implements a two-alternative choice task with two lick ports.

Defines the following:
* param_abbrevs, which defines the shorthand for the trial parameters
* param_values, which define the defaults for those parameters
* contains stepper rotation functions

*/


#include "States.h"
#include "Arduino.h"
#include "hwconstants.h"

#ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
#include "Stepper.h"
#endif

#ifndef __HWCONSTANTS_H_USE_IR_DETECTOR
#include "mpr121.h"
#endif


// include this one just to get __TRIAL_SPEAK_YES
#include "chat.h"



// These should go into some kind of Protocol.h or something


char* param_abbrevs[N_TRIAL_PARAMS] = {
  "SRVFAR", "SRVST", "STPSPD", "STPIP",
};

long param_values[N_TRIAL_PARAMS] = {
  1900, 1000, 20, 50,
};

// Whether to report on each trial  
// Currently, manually match this up with Python-side
// Later, maybe make this settable by Python, and default to all True
// Similarly, find out which are required on each trial, and error if they're
// not set. Currently all that are required_ET are also reported_ET.
bool param_report_ET[N_TRIAL_PARAMS] = {
  1, 1, 1, 1,
};
  

// Global, persistent variable to remember where the stepper is
long sticky_stepper_position = 0;

//Horizontal position (maximum voltage)
long horizontal_position;


//// State definitions
#ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
extern Stepper* stimStepper;
#endif

int findStepperPeak() {
  //Find the maximum value of sensor through full rotation
  int n_steps = 200;
  long nondirectional_steps = 0;
  int sensor_history[200] = {0};
  int sensor;

  #ifdef __HWCONSTANTS_H_USE_STEPPER_DRIVER
  #ifdef __HWCONSTANTS_H_INVERT_STEPPER_DIRECTION
  // Step forwards or backwards
  if (step_size < 0) {
    nondirectional_steps = -n_steps * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, HIGH);
  } else {
    nondirectional_steps = n_steps * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, LOW);
  }  
  #endif
  
  #ifndef __HWCONSTANTS_H_INVERT_STEPPER_DIRECTION
  // Step forwards or backwards
  if (n_steps < 0) {
    nondirectional_steps = -n_steps * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, LOW);
  } else {
    nondirectional_steps = n_steps * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, HIGH);
  }    
  #endif
  #endif
  
  //Rotate 360 degrees and record sensor voltages
  for (int i = 0; i < nondirectional_steps; i++) {
    #ifdef __HWCONSTANTS_H_USE_STEPPER_DRIVER
    rotate_one_step();
    #endif

    #ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
    stimStepper->step(1);
    #endif
    sensor = analogRead(__HWCONSTANTS_H_HALL1);
    sensor_history[i / __HWCONSTANTS_H_MICROSTEP] = sensor;
  }

  Serial.print(millis());
  Serial.print(" SENH ");
  for (int i=0; i < n_steps; i++) {
    Serial.print(sensor_history[i]);
    Serial.print(" ");
  }
  Serial.println("");

  //Find max value of recorded sensor values
  int steps_away = steps_to_max(sensor_history, n_steps);
  if (steps_away > 100) {
    steps_away = steps_away -100;
  }

  horizontal_position = (sticky_stepper_position + steps_away + 200) % 200;


  return 0;

}

int steps_to_max(int a[], int size) {
  // Calculates distance from max sensor value
  int max = 0;
  int max_index = 0;

  for (int i = 0; i < size; i++) {
    
    if (a[i] > max) {
      max = a[i];
      max_index = i;
    }
  }

  return max_index;
}

int rotate_to_sensor2() {
  //Rotate to pre-recorded Hall sensor peak
  //Alternate method
  if (sticky_stepper_position > horizontal_position) {
    rotate(horizontal_position - sticky_stepper_position);
  }
  else {
    rotate(sticky_stepper_position - horizontal_position);
  }
  return 0;
} 
  

int rotate_to_sensor(int step_size, bool positive_peak, long set_position,
  int hall_sensor_id)
{ /* Rotate to a position where the Hall effect sensor detects a peak.
  
  step_size : typically 1 or -1, the number of steps to use between checks
  positive_peak : whether to stop when a positive or negative peak detected
  set_position : will set "sticky_stepper_position" to this afterwards
  hall_sensor_id : 1 or 2, depending on which hall sensor to read
  */
  bool keep_going = 1;
  int sensor;
  int prev_sensor = sensor;
  int actual_steps = 0;
  #ifdef __HWCONSTANTS_H_USE_STEPPER_DRIVER
  long nondirectional_steps = 0;
  #endif
  
  // Keep track of the previous values
  int sensor_history[__HWCONSTANTS_H_SENSOR_HISTORY_SZ] = {0};
  int sensor_history_idx = 0;
  
  if (hall_sensor_id == 1) {
    sensor = analogRead(__HWCONSTANTS_H_HALL1);
  } else if (hall_sensor_id == 2) {
    sensor = analogRead(__HWCONSTANTS_H_HALL2);
  }
  
  // Store in circular buffer
  sensor_history[sensor_history_idx] = sensor;
  sensor_history_idx = (sensor_history_idx + 1) % 
    __HWCONSTANTS_H_SENSOR_HISTORY_SZ;
  
  #ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
  digitalWrite(TWOPIN_ENABLE_STEPPER, HIGH);
  delay(__HWCONSTANTS_H_STP_POST_ENABLE_DELAY);
  #endif

  
  #ifdef __HWCONSTANTS_H_USE_STEPPER_DRIVER
  #ifdef __HWCONSTANTS_H_INVERT_STEPPER_DIRECTION
  // Step forwards or backwards
  if (step_size < 0) {
    nondirectional_steps = -step_size * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, HIGH);
  } else {
    nondirectional_steps = step_size * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, LOW);
  }  
  #endif
  
  #ifndef __HWCONSTANTS_H_INVERT_STEPPER_DIRECTION
  // Step forwards or backwards
  if (step_size < 0) {
    nondirectional_steps = -step_size * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, LOW);
  } else {
    nondirectional_steps = step_size * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, HIGH);
  }    
  #endif
  #endif


  // iterate till target found
  while (keep_going)
  {
    // Rotate the correct number of steps
    #ifdef __HWCONSTANTS_H_USE_STEPPER_DRIVER
    for (int i=0; i<nondirectional_steps; i++) {
      rotate_one_step();
    }
    #endif
    
    #ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
    stimStepper->step(step_size);
    #endif
    
    actual_steps += step_size;
    
    // update sensor and store previous value
    prev_sensor = sensor;
    if (hall_sensor_id == 1) {
      sensor = analogRead(__HWCONSTANTS_H_HALL1);
    } else if (hall_sensor_id == 2) {
      sensor = analogRead(__HWCONSTANTS_H_HALL2);
    }

    // Store in circular buffer
    sensor_history[sensor_history_idx] = sensor;
    sensor_history_idx = (sensor_history_idx + 1) % 
      __HWCONSTANTS_H_SENSOR_HISTORY_SZ;    
    
    // test if peak found
    if (positive_peak && (prev_sensor > (512 + __HWCONSTANTS_H_HALL_THRESH)) && ((sensor - prev_sensor) < -2))
    {
        // Positive peak: sensor is high, but decreasing
        keep_going = 0;
    }
    else if (!positive_peak && (prev_sensor < (512 - __HWCONSTANTS_H_HALL_THRESH)) && ((sensor - prev_sensor) > 2))
    {
        // Negative peak: sensor is low, but increasing
        keep_going = 0;
    }
    
    // Quit if >400 steps have been taken
    if (abs(actual_steps) > 400) {
      Serial.print(millis());
      Serial.println(" DBG STEPS400");
      keep_going = 0;
    }
  }

  // Dump the circular buffer
  Serial.print(millis());
  Serial.print(" SENH ");
  for (int i=0; i<__HWCONSTANTS_H_SENSOR_HISTORY_SZ; i++) {
    Serial.print(sensor_history[
      (sensor_history_idx + i + 1) % __HWCONSTANTS_H_SENSOR_HISTORY_SZ]);
    Serial.print(" ");
  }
  Serial.println("");

  // Undo the last step to reach peak exactly
  #ifdef __HWCONSTANTS_H_USE_STEPPER_DRIVER
  #ifdef __HWCONSTANTS_H_INVERT_STEPPER_DIRECTION
  // Step forwards or backwards
  if (step_size < 0) {
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, LOW);
  } else {
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, HIGH);
  }  
  #endif
  
  #ifndef __HWCONSTANTS_H_INVERT_STEPPER_DIRECTION
  // Step forwards or backwards
  if (step_size < 0) {
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, HIGH);
  } else {
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, LOW);
  }    
  #endif
  
  rotate_one_step();
  #endif
  
  
  // Disable H-bridge to prevent overheating
  #ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
  digitalWrite(TWOPIN_ENABLE_STEPPER, LOW);
  #endif

  // update to specified position
  sticky_stepper_position = set_position;

  return actual_steps;
}

int rotate(long n_steps)
{ /* Low-level rotation function 
  
  I think positive n_steps means CCW and negative n_steps means CW. It does
  on L2, at least.
  */
  
  
  #ifdef __HWCONSTANTS_H_USE_STEPPER_DRIVER
  // This incorporates microstepping and will always be positive
  long nondirectional_steps = 0;
  
  #ifdef __HWCONSTANTS_H_INVERT_STEPPER_DIRECTION
  // Step forwards or backwards
  if (n_steps < 0) {
    nondirectional_steps = -n_steps * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, HIGH);
  } else {
    nondirectional_steps = n_steps * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, LOW);
  }  
  #endif
  
  #ifndef __HWCONSTANTS_H_INVERT_STEPPER_DIRECTION
  // Step forwards or backwards
  if (n_steps < 0) {
    nondirectional_steps = -n_steps * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, LOW);
  } else {
    nondirectional_steps = n_steps * __HWCONSTANTS_H_MICROSTEP;
    digitalWrite(__HWCONSTANTS_H_STEP_DIR, HIGH);
  }    
  #endif
  
  // Rotate the correct number of steps
  for (int i=0; i<nondirectional_steps; i++) {
    rotate_one_step();
  }
  #endif


  #ifndef __HWCONSTANTS_H_USE_STEPPER_DRIVER
  // Enable the stepper according to the type of setup
  digitalWrite(TWOPIN_ENABLE_STEPPER, HIGH);

  // Sometimes the stepper spins like crazy without a delay here
  delay(__HWCONSTANTS_H_STP_POST_ENABLE_DELAY);
  
  // BLOCKING CALL //
  // Replace this with more iterations of smaller steps
  stimStepper->step(n_steps);

  // Disable H-bridge to prevent overheating
  delay(__HWCONSTANTS_H_STP_POST_ENABLE_DELAY);
  digitalWrite(TWOPIN_ENABLE_STEPPER, LOW);
  #endif
 
 
  // update sticky_stepper_position
  sticky_stepper_position = sticky_stepper_position + n_steps;
  
  // keep it in the range [0, 200)
  sticky_stepper_position = (sticky_stepper_position + 200) % 200;
  
  return 0;
}

#ifdef __HWCONSTANTS_H_USE_STEPPER_DRIVER
void rotate_one_step()
{ // Pulse the step pin, then delay the specified number of microseconds
  digitalWrite(__HWCONSTANTS_H_STEP_PIN, HIGH);
  delayMicroseconds(__HWCONSTANTS_H_STEP_HALFDELAY_US / 
    __HWCONSTANTS_H_MICROSTEP);
  digitalWrite(__HWCONSTANTS_H_STEP_PIN, LOW);
  delayMicroseconds(__HWCONSTANTS_H_STEP_HALFDELAY_US / 
    __HWCONSTANTS_H_MICROSTEP);  
}
#endif



