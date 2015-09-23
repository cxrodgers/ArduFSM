// implementations for ir detector sampling functions
// supposed to be a drop-in replacement for mpr121

#include "ir_detector.h"
#include "Arduino.h"

// Just to get thresholds
#include "States.h"
extern long param_values[N_TRIAL_PARAMS];


int get_touched_channel(uint16_t touched, unsigned int i)
{
  return (touched & (1 << i)) >> i;
}

uint16_t pollTouchInputs(unsigned long time, bool debug)
{ /* Samples both ir pins and returns whether they are touched.
  
  Stores a recent history of values on both pins in two circular buffers.
  The buffers are updated every __IR_DETECTOR_H_UPDATE_T ms and contains
  __IR_DETECTOR_H_BUFFER_SZ data points. If the current value is less
  than the mean of the buffer minus __IR_DETECTOR_H_L_THRESH (or
  __IR_DETECTOR_H_R_THRESH for the right pipe), then `touched` is set
  to true for that channel.
  
  This buffer should be long enough that it isn't confused by recent
  events (such as a lot of licking), but not so long that it can't
  compensate for slow changes in luminance. Maybe 5 seconds?
  
  Possible improvement: if the mean value is less than the threshold
  already, then it will be impossible to detect licks. Lower threshold
  to 50% of mean in this case, but not below some hard cutoff.
  
  Can also issue a debug print statement that contains the current value,
  the current mean of the buffer, and the minimum value seen since the
  last time the debug statement was printed.
  
  
  
  */
  // Circular buffers 
  static int l_buffer[__IR_DETECTOR_H_BUFFER_SZ];
  static int r_buffer[__IR_DETECTOR_H_BUFFER_SZ];
  
  // Flag for init
  static bool l_buffer_init = 0;
  static bool r_buffer_init = 0;
  
  // Flag for current index
  static int l_buffer_idx = 0;
  static int r_buffer_idx = 0;
  
  // Last update time
  static unsigned long int last_update_time = 0;

  // Cached running mean
  static long l_mean = 0;
  static long r_mean = 0;
  
  // Cached min
  static int l_min = 1023;
  static int r_min = 1023;
  
  // New values
  int l_val = analogRead(__HWCONSTANTS_H_IR_L_PIN);
  int r_val = analogRead(__HWCONSTANTS_H_IR_R_PIN);
  int ltemp = 0;
  
  // Return value
  uint16_t touched = 0;
  
  // Init the buffers
  if (!l_buffer_init) {
    for (int i=0; i<__IR_DETECTOR_H_BUFFER_SZ; i++) {
      l_buffer[i] = 512;
    }
    l_buffer_init = 1;
  }
  if (!r_buffer_init) {
    for (int i=0; i<__IR_DETECTOR_H_BUFFER_SZ; i++) {
      r_buffer[i] = 512;
    }
    r_buffer_init = 1;
  }

  // Update the buffers every __IR_DETECTOR_H_UPDATE_T ms
  if (last_update_time + __IR_DETECTOR_H_UPDATE_T < time) {
    last_update_time = time;
    l_buffer[l_buffer_idx] = l_val;
    l_buffer_idx = (l_buffer_idx + 1) % __IR_DETECTOR_H_BUFFER_SZ;
    r_buffer[r_buffer_idx] = r_val;
    r_buffer_idx = (r_buffer_idx + 1) % __IR_DETECTOR_H_BUFFER_SZ;

    // Update the mean
    l_mean = 0;
    for (int i=0; i<__IR_DETECTOR_H_BUFFER_SZ; i++) {
      l_mean += l_buffer[i];
    }  
    l_mean = l_mean / __IR_DETECTOR_H_BUFFER_SZ;
    r_mean = 0;
    for (int i=0; i<__IR_DETECTOR_H_BUFFER_SZ; i++) {
      r_mean += r_buffer[i];
    }  
    r_mean = r_mean / __IR_DETECTOR_H_BUFFER_SZ;
  }

  // Normalize
  ltemp = l_val - (r_val - r_mean);
  r_val = r_val - (l_val - l_mean);
  l_val = ltemp;
  
  // Debug
  if (debug) {
    Serial.print(time);
    Serial.print(" DBG L:c=");
    Serial.print(l_val);
    Serial.print(";m=");
    Serial.print(l_mean);
    Serial.print(";x=");
    Serial.print(l_min);    
    Serial.println(".");
    Serial.print(time);
    Serial.print(" DBG R:c=");
    Serial.print(r_val);
    Serial.print(";m=");
    Serial.print(r_mean);
    Serial.print(";x=");
    Serial.print(r_min);        
    Serial.println(".");
    
    // reset debugging info
    l_min = 1023;
    r_min = 1023;
  }
  
  // Check whether a new minimum was set (only for debugging info)
  if (l_val < l_min)
    l_min = l_val;
  if (r_val < r_min)
    r_min = r_val;
  
  // Check whether each fell by THRESH from the mean
  if (l_val < l_mean - param_values[tpidx_TOU_THRESH]) //__IR_DETECTOR_H_L_THRESH)
    touched += 1;
  if (r_val < r_mean - param_values[tpidx_REL_THRESH]) //__IR_DETECTOR_H_R_THRESH)
    touched += 2;
  
  return touched;
}  
