#include "States.h"
#include "mpr121.h"
#include "Arduino.h"
#include "hwconstants.h"
#include "Stepper.h"

extern STATE_TYPE next_state;
extern unsigned int rewards_this_trial;
String param_abbrevs[N_TRIAL_PARAMS] = {
  "STPPOS", "MRT", "RWSD", "SRVPOS", "ITI",
  "2PSTP", "SRVFAR", "SRVTT", "RWIN", "IRI",
  "RD_L", "RD_R", "SRVST", "PSW", "TOE",
  "TO", "STPSPD", "STPFR", "STPIP",
  };
long param_values[N_TRIAL_PARAMS] = {
  1, 1, 1, 1, 3000,
  -1, 1900, 4500, 45000, 500,
  40, 40, 2000, 1, 1,
  2000, 20, 50, 50,
  };


String results_abbrevs[N_TRIAL_RESULTS] = {"RESP", "OUTC"};
long results_values[N_TRIAL_RESULTS] = {0, 0};
long default_results_values[N_TRIAL_RESULTS] = {0, 0};

long state_timer = -1;
long sticky_stepper_position = param_values[tpidx_STEP_INITIAL_POS];  


//// State definitions
extern Stepper stimStepper;

void StateResponseWindow::s_setup()
{
  
}

void StateResponseWindow::loop(uint16_t touched)
{
  int current_response;
  bool licking_l;
  bool licking_r;
  
  licking_l = (get_touched_channel(touched, 0) == 1);
  licking_r = (get_touched_channel(touched, 1) == 1);
  // transition if max rewards reached
  if (rewards_this_trial >= param_values[tpidx_MRT])
  {
    next_state = PRE_SERVO_WAIT;
    flag_stop = 1;
    return;
  }

  // Do nothing if both or neither are being licked.
  // Otherwise, assign current_response.
  if (!licking_l && !licking_r)
    return;
  else if (licking_l && licking_r)
    return;
  else if (licking_l && !licking_r)
    current_response = LEFT;
  else if (!licking_l && licking_r)
    current_response = RIGHT;
  else
    Serial.println("this should never happen");

  // Only assign result if this is the first response
  if (results_values[tridx_RESPONSE] == 0)
    results_values[tridx_RESPONSE] = current_response;
  
  // Move to reward state, or error if TOE is set, or otherwise stay
  if ((current_response == LEFT) && (param_values[tpidx_REWSIDE] == LEFT))
    next_state = REWARD_L;
  else if ((current_response == RIGHT) && (param_values[tpidx_REWSIDE] == RIGHT))
    next_state = REWARD_L;
  else if (param_values[tpidx_TERMINATE_ON_ERR] == 2)
    next_state = ERROR;
}

void StateResponseWindow::s_finish()
{
  // If response is still not set, mark as spoiled
  if (results_values[tridx_RESPONSE] == 0)
    results_values[tridx_RESPONSE] = NOGO;

  next_state = INTER_TRIAL_INTERVAL;
}


int state_inter_rotation_pause(unsigned long time, long state_duration,
    STATE_TYPE& next_state)
{
  // Wait the specified amount of time
  if (state_timer == -1)
  {
    // Start timer and run first-time code
    state_timer = time + state_duration; // hard coded 50ms pause

    //a_waiting_state_run_once();
  }
  else
  {
    //a_waiting_state_run_many_times();
  }
  
  if (time > state_timer)
  {
    //a_waiting_state_run_when_done();
    
    // Check timer and run every-time code
    next_state = ROTATE_STEPPER2;
    state_timer = 0;
  }
  
  return 0;
}

int state_wait_for_servo_move(unsigned long time, unsigned long timer,
    STATE_TYPE& next_state)
{
  //a_waiting_state_run_many_times();
  
  if (time > timer)
  {
    //a_waiting_state_run_when_done();
    
    // Check timer and run every-time code
    next_state = RESPONSE_WINDOW;
    timer = 0;
  }
  
  return 0;  
}


int state_rotate_stepper1(STATE_TYPE& next_state)
{
  rotate(param_values[tpidx_STEP_FIRST_ROTATION]);
  next_state = INTER_ROTATION_PAUSE;
  return 0;    
}

int state_rotate_stepper2(STATE_TYPE& next_state)
{
  int remaining_rotation = param_values[tpidx_STPPOS] - 
    param_values[tpidx_STEP_FIRST_ROTATION] - sticky_stepper_position;
  
  rotate(remaining_rotation);
  
  next_state = WAIT_FOR_SERVO_MOVE;
  return 0;    
}

int rotate(long n_steps)
{
  // rotate_motor(param_values[tpidx_STEP_FIRST_ROTATION], 20);
  if (param_values[tpidx_2PSTP])
  {
    digitalWrite(TWOPIN_ENABLE_STEPPER, HIGH);
  }
  else
  {
    digitalWrite(ENABLE_STEPPER, HIGH);
  }
  
  // pause?
  
  // BLOCKING CALL //
  // Replace with more iterations of smaller steps
  stimStepper.step(n_steps);
  
  // pause?
  
  // disable
  if (param_values[tpidx_2PSTP])
  {
    digitalWrite(TWOPIN_ENABLE_STEPPER, LOW);
  }
  else
  {
    digitalWrite(ENABLE_STEPPER, LOW);
  }    
  
  return 0;
}
