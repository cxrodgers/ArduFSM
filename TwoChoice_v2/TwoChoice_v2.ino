/* Simple protocol to test the setting of trial-by-trial settings.

Waits to receive a rewarded side, and maybe some other stuff.
Randomly generates a response.

TODO
----
* Move the required states, like TRIAL_START and WAIT_FOR_NEXT_TRIAL,
  as well as all required variables like flag_start_trial, into TrialSpeak.cpp.
* Some standard way to create waiting states.
* move definitions of trial_params to header file, so can be auto-generated
* diagnostics: which state it is in on each call (or subset of calls)

Here are the things that the user should have to change for each protocol:
* Enum of states
* User-defined states in switch statement
* param_abbrevs, param_values, tpidx_*, N_TRIAL_PARAMS


*/
#include "chat.h"
#include "hwconstants.h"
#include "mpr121.h"
#include <Wire.h> # also for mpr121
#include <Servo.h>
#include <Stepper.h>
#include "TimedState.h"

//// Defines for commonly used things
// Move this to TrialSpeak
#define LEFT 1
#define RIGHT 2
#define NOGO 3

//// States
// Defines the finite state machine for this protocol
enum STATE_TYPE
{
  WAIT_TO_START_TRIAL,
  TRIAL_START,
  ROTATE_STEPPER1,
  INTER_ROTATION_PAUSE,
  ROTATE_STEPPER2,
  MOVE_SERVO,
  WAIT_FOR_SERVO_MOVE,
  RESPONSE_WINDOW,
  REWARD_L,
  REWARD_R,
  POST_REWARD_TIMER_START,
  POST_REWARD_TIMER_WAIT,
  START_INTER_TRIAL_INTERVAL,
  INTER_TRIAL_INTERVAL,
  ERROR,
  PRE_SERVO_WAIT,
  SERVO_WAIT
} current_state = WAIT_TO_START_TRIAL;


//// Global trial parameters structure. This holds the current value of
// all parameters. Should probably also make a copy to hold the latched
// values on each trial.
// Characteristics of each trial. These can all be modified by the user.
// However, there is no guarantee that the newest value will be used until
// the current trial is released.
// Various types:
// * Should be latched, must be set at beginning ("RD_L")
// * Should be latched, can use default here ("SRVFAR")
// * Need to be set on every trial, else error ("STPPOS")
// Attempt to have 0 be the "error value" since it cannot intentially be set to 0.
#define N_TRIAL_PARAMS 19
#define tpidx_STPPOS 0
#define tpidx_MRT 1
#define tpidx_REWSIDE 2
#define tpidx_SRVPOS 3
#define tpidx_ITI 4
#define tpidx_2PSTP 5
#define tpidx_SRV_FAR 6
#define tpidx_SRV_TRAVEL_TIME 7
#define tpidx_RESP_WIN_DUR 8
#define tpidx_INTER_REWARD_INTERVAL 9
#define tpidx_REWARD_DUR_L 10
#define tpidx_REWARD_DUR_R 11
#define tpidx_SERVO_SETUP_T 12
#define tpidx_PRE_SERVO_WAIT 13
#define tpidx_TERMINATE_ON_ERR 14
#define tpidx_ERROR_TIMEOUT 15
#define tpidx_STEP_SPEED 16
#define tpidx_STEP_FIRST_ROTATION 17
#define tpidx_STEP_INITIAL_POS 18
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


//// Global trial results structure. Can be set by user-defined states. 
// Will be reported during mandatory INTER_TRIAL_INTERVAL state.
#define N_TRIAL_RESULTS 2
#define tridx_RESPONSE 0
#define tridx_OUTCOME 1
String results_abbrevs[N_TRIAL_RESULTS] = {"RESP", "OUTC"};
long results_values[N_TRIAL_RESULTS] = {0, 0};
long default_results_values[N_TRIAL_RESULTS] = {0, 0};


//// Miscellaneous globals
// Debugging announcements
unsigned long speak_at = 1000;
unsigned long interval = 1000;

// flag to remember whether we've received the start next trial signal
bool flag_start_trial = 0;

// timers
long state_timer = -1;


//// Declarations
int take_action(String protocol_cmd, String argument1);



//// User-defined variables, etc, go here
unsigned int rewards_this_trial = 0;
long servo_timer;
STATE_TYPE next_state; 

// touched monitor
uint16_t sticky_touched = 0;

// initial position of stim arm .. user must ensure this is correct
long sticky_stepper_position = param_values[tpidx_STEP_INITIAL_POS];

// Servo
Servo linServo;

// Stepper
// TODO: do not assign now, because we might set it up as a 2-pin stepper later
Stepper stimStepper = Stepper(200, PIN_STEPPER1, PIN_STEPPER2, PIN_STEPPER3, PIN_STEPPER4);

// Declare
void rotate_motor(int rotation, unsigned int delay_ms=100);
int state_inter_rotation_pause(unsigned long time, long state_duration,
    STATE_TYPE& next_state);
int state_rotate_stepper1(STATE_TYPE& next_state);
int state_rotate_stepper2(STATE_TYPE& next_state);
int state_wait_for_servo_move(unsigned long time, unsigned long timer,
    STATE_TYPE& next_state);

//// State definitions
class StateResponseWindow : public TimedState {
  protected:
    int var = 0;  
    void s_setup();  
    void loop(uint16_t touched);
    void s_finish();
  
  public:
    StateResponseWindow(unsigned long t, unsigned long d) : TimedState(t, d) { };
};

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


//// Setup function
void setup()
{
  unsigned long time = millis();
  int status = 1;
  
  Serial.begin(115200);
  Serial.println((String) time + " DBG begin setup");

  //// Begin user protocol code
  //// Put this in a user_setup1() function?
  
  // MPR121 touch sensor setup
  pinMode(TOUCH_IRQ, INPUT);
  digitalWrite(TOUCH_IRQ, HIGH); //enable pullup resistor
  Wire.begin();
  mpr121_setup(TOUCH_IRQ);
  
  // output pins
  pinMode(L_REWARD_VALVE, OUTPUT);
  pinMode(R_REWARD_VALVE, OUTPUT);
  
  // random number seed
  randomSeed(analogRead(3));

  // attach servo
  linServo.attach(LINEAR_SERVO);

  
  //// Run communications until we've received all setup info
  // Later make this a new flag. For now wait for first trial release.
  while (!flag_start_trial)
  {
    status = communications(time);
    if (status != 0)
    {
      Serial.println("comm error in setup");
      delay(1000);
    }
  }
  
  
  //// Now finalize the setup using the received initial parameters
  // user_setup2() function?
  
  // Set up the stepper according to two-pin or four-pin mode
  if (param_values[tpidx_2PSTP] == 1)
  { // Two-pin mode
    pinMode(TWOPIN_ENABLE_STEPPER, OUTPUT);
    pinMode(TWOPIN_STEPPER_1, OUTPUT);
    pinMode(TWOPIN_STEPPER_2, OUTPUT);
    
    // Make sure it's off    
    digitalWrite(TWOPIN_ENABLE_STEPPER, LOW); 
    
    // Initialize
    stimStepper = Stepper(param_values[tpidx_STEP_SPEED], 
      TWOPIN_STEPPER_1, TWOPIN_STEPPER_2);
  }
  else
  { // Four-pin mode
    pinMode(ENABLE_STEPPER, OUTPUT);
    pinMode(PIN_STEPPER1, OUTPUT);
    pinMode(PIN_STEPPER2, OUTPUT);
    pinMode(PIN_STEPPER3, OUTPUT);
    pinMode(PIN_STEPPER4, OUTPUT);
    digitalWrite(ENABLE_STEPPER, LOW); // # Make sure it's off
    
    stimStepper = Stepper(param_values[tpidx_STEP_SPEED], 
      PIN_STEPPER1, PIN_STEPPER2, PIN_STEPPER3, PIN_STEPPER4);
  }

  // linear servo setup
  linServo.write(param_values[tpidx_SRV_FAR]);
  delay(param_values[tpidx_SERVO_SETUP_T]);
}


int communications(unsigned long time)
{ /* Run the chat receiving and debug announcing stuff, independent of
    any state machine or user protocol stuff.
  
    Announces time, as necessary.
    Receives any chat and handles it, including calling take_action.
  */
  // comm variables
  String received_chat;
  String protocol_cmd = (String) "";
  String argument1 = (String) "";
  String argument2 = (String) "";
  int status = 1;
  
  
  //// Perform actions that occur on every call, independent of state
  // Announce the time
  if (time >= speak_at)
  {
    Serial.println((String) time + " DBG");
    speak_at += interval;
  }

  //// Receive and deal with chat
  received_chat = receive_chat();
  if (received_chat.length() > 0)
  {
    // Attempt to parse
    status = handle_chat(received_chat, flag_start_trial,
        protocol_cmd, argument1, argument2);
    if (status != 0)
    {
      // Parse/syntax error
      Serial.println((String) time + " DBG RC_ERR " + (String) status);
    }
    else if (protocol_cmd.length() > 0)
    {
      // Protocol action required
      status = take_action(protocol_cmd, argument1, argument2);
      
      if (status != 0)
      {
        // Parse/syntax error
        Serial.println((String) time + " DBG TA_ERR " + (String) status);
      }
    }
  }
  
  return 0;
}


//// Loop function
void loop()
{ /* Called over and over again. On each call, the behavior is determined
     by the current state.
  */
  
  //// Variable declarations
  // get the current time as early as possible in this function
  unsigned long time = millis();
  
  // The next state, by default the same as the current state
  next_state = current_state;
  
  // misc
  int status = 1;
  
  
  //// User protocol variables
  uint16_t touched = 0;
  
  
  //// Run communications
  status = communications(time);
  
  
  //// User protocol code
  // could put other user-specified every_loop() stuff here
  
  // Poll touch inputs
  touched = pollTouchInputs();
  
  // announce sticky
  if (touched != sticky_touched)
  {
    Serial.println((String) time + " TCH " + touched);
    sticky_touched = touched;
  }  
  

  //// Begin state-dependent operations
  switch (current_state)
  {
    //// Wait till the trial is released. Same for all protocols.
    case WAIT_TO_START_TRIAL:
      // Wait until we receive permission to continue  
      if (flag_start_trial)
      {
        // Announce that we have ended the trial and reset the flag
        Serial.println((String) time + " TRL_RELEASED");
        flag_start_trial = 0;
        
        // Proceed to next trial
        next_state = TRIAL_START;
      }
      break;

    //// TRIAL_START. Same for all protocols.
    case TRIAL_START:
      // Set up the trial based on received trial parameters
      Serial.println((String) time + " TRL_START");
      for(int i=0; i < N_TRIAL_PARAMS; i++)
      {
        Serial.println((String) time + " TRLP " + (String) param_abbrevs[i] + 
          " " + (String) param_values[i]);
      }
    
      // Set up trial_results to defaults
      for(int i=0; i < N_TRIAL_RESULTS; i++)
      {
        results_values[i] = default_results_values[i];
      }      
      
      
      //// User-defined code goes here
      // declare the states
      static StateResponseWindow srw(0, param_values[tpidx_RESP_WIN_DUR]);
      
      // Could have it's own state, really
      rewards_this_trial = 0;
    
      next_state = MOVE_SERVO;
      break;
    
    
    //// Example of a complex waiting state
    // We want to start the servo moving, rotate while moving,
    // start response window when the timer is up.
    case MOVE_SERVO:
      linServo.write(param_values[tpidx_SRVPOS]);
      servo_timer = time + param_values[tpidx_SRV_TRAVEL_TIME];
      next_state = ROTATE_STEPPER1;
      break;
    
    case ROTATE_STEPPER1:
      state_rotate_stepper1(next_state);
      break;
    
    case INTER_ROTATION_PAUSE:
      state_inter_rotation_pause(time, 50, next_state);
      break;
    
    case ROTATE_STEPPER2:
      state_rotate_stepper2(next_state);
      break;

    case WAIT_FOR_SERVO_MOVE:
      state_wait_for_servo_move(time, servo_timer, next_state);
      break;
    
    case RESPONSE_WINDOW:
      srw.run(time, touched);
      break;
    
    case REWARD_L:
      Serial.println((String) time + " DBG open L");
      state_timer = -1;
      next_state = INTER_TRIAL_INTERVAL;
      break;
    
    case REWARD_R:
      Serial.println((String) time + " DBG open R");
    state_timer = -1;
      next_state = INTER_TRIAL_INTERVAL;
      break;
    
    case ERROR:
      Serial.println((String) time + " DBG error");
    state_timer = -1;
      next_state = INTER_TRIAL_INTERVAL;
      break;
      
    
    //// INTER_TRIAL_INTERVAL
    // Example of canonical waiting state.
    // Also announced trial_results.
    case INTER_TRIAL_INTERVAL:
      // Wait the specified amount of time
      if (state_timer == -1)
      {
        // Start timer and run first-time code
        state_timer = time + param_values[tpidx_ITI];

        // First-time code: Report results
        for(int i=0; i < N_TRIAL_RESULTS; i++)
        {
          Serial.println((String) time + " TRLR " + (String) results_abbrevs[i] + 
            " " + (String) results_values[i]);
        }
      }
      if (time > state_timer)
      {
        // Check timer and run every-time code
        next_state = WAIT_TO_START_TRIAL;
        state_timer = -1;
      }
      break;
  }
  
  
  //// Update the state variable
  if (next_state != current_state)
  {
    Serial.println((String) time + " ST_CHG " + current_state + " " + next_state);
  }
  current_state = next_state;
  
  return;
}


//// Take protocol action based on user command (ie, setting variable)
int take_action(String protocol_cmd, String argument1, String argument2)
{ /* Protocol action.
  
  Currently the only possible action is setting a parameter. In this case,
  protocol_cmd must be "SET". argument1 is the variable name. argument2 is
  the data.
  
  This logic could be incorporated in TrialSpeak, but we would need to provide
  the abbreviation, full name, datatype, and optional handling logic for
  each possible variable. So it seems to make more sense here.
  
  Return values:
  0 - command parsed successfully
  2 - unimplemented protocol_cmd
  4 - unknown variable on SET command
  5 - data conversion error
  */
  int status;
  
  if (protocol_cmd == "SET")
  {
    // Find index into param_abbrevs
    int idx = -1;
    for (int i=0; i < N_TRIAL_PARAMS; i++)
    {
      if (param_abbrevs[i] == argument1)
      {
        idx = i;
        break;
      }
    }
    
    // Error if not found, otherwise set
    if (idx == -1)
    {
      return 4;
    }
    else
    {
      // Convert to int
      status = safe_int_convert(argument2, param_values[idx]);
      if (status != 0)
      {
        return 5;
      }
    }
  }    
  else
  {
    // unknown command
    return 2;
  }
  
  return 0;
}


int safe_int_convert(String string_data, long &variable)
{ /* Check that string_data can be converted to int before setting variable.
  
  Currently, variable cannot be set to 0 using this script. That is because
  toInt returns 0 upon error condition.
  
  Not sure how to handle the case when variable is some other kind of int?
  
  Returns 1 if string data converts to 0 (ie, an error occurs).
  */
  int conversion_var = string_data.toInt();
  if (conversion_var == 0)
  {
    return 1;
  }
  else 
  {
    variable = conversion_var;
  }  
  return 0;
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

  


