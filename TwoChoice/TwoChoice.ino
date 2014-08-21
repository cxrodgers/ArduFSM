#include "chat.h"
#include "mpr121.h"
#include <Wire.h> # also for mpr121
#include <Servo.h>
#include <Stepper.h>


bool USE_LEVER = 0;
bool TWO_PIN_STEPPER = 0;

// At most one of the following lines should be uncommented
#define SIX_STIM 1
//#define FOUR_STIM 1

// Pins
struct PINS_TYPE 
{
  // Two-pin stepper mode
  static const unsigned int TWOPIN_ENABLE_STEPPER = 11; // to turn on stepper
  static const unsigned int TWOPIN_STEPPER_1 = 12;
  static const unsigned int TWOPIN_STEPPER_2 = 13; // to turn on stepper
  
  
  // Digital outputs
  static const unsigned int ENABLE_STEPPER = 12; // to turn on stepper
  static const unsigned int LINEAR_SERVO = 4; // to control servo
  static const unsigned int REWARD_VALVE = 7; // to operate valve
  static const unsigned int SPEAKER = 5; // PWM speaker
  
  // Digital inputs (???)
  static const unsigned int TOUCH_IRQ = 2; // to receive touch interrupts
  
  // Analog inputs
  static const unsigned int LEVER_L = 2;
  static const unsigned int LEVER_R = 1;
} PINS;

// States
enum STATE_TYPE
{
  TRIAL_START,
  MOVE_SERVO_START,
  MOVE_SERVO_WAIT,
  RESPONSE_WINDOW_START,
  RESPONSE_WINDOW,
  REWARD_L,
  REWARD_R,
  REWARD_TIMER_L,
  REWARD_TIMER_R,
  POST_REWARD_TIMER_START,
  POST_REWARD_TIMER_WAIT,
  START_INTER_TRIAL_INTERVAL,
  INTER_TRIAL_INTERVAL,
  ERROR,
  PRE_SERVO_WAIT,
  SERVO_WAIT
} current_state = TRIAL_START;


// Locations of the servo
struct SERVO_POSITIONS_TYPE 
{
  static const int NEAR = 1150; // position when within whisking range
  static const int FAR = 1900; // position when out of whisking range
  int POS_DELTA = 25; // distance between positions
  static const unsigned long NEAR2FAR_TRAVEL_TIME = 3500;
} SERVO_POSITIONS;

// Trial variables
struct TRIAL_PARAMS_TYPE
{
  char rewarded_side = 'L';
  String outcome = "spoil";
  String choice = "nogo";
  int servo_position = SERVO_POSITIONS.NEAR;
  int stim_number = 0;
} current_trial_params;

// Session params -- combine this with trial variables
struct SESSION_PARAMS_TYPE
{
  char force = 'X';
  unsigned long inter_trial_interval = 3500; // Ensure this is > NEAR2FAR_TRAVEL_TIME for now
  unsigned long response_window_dur = 45000;
  unsigned long inter_reward_interval = 500; // assuming multiple rewards in response window possible
  unsigned long reward_dur_l = 40;
  unsigned long reward_dur_r = 50;  
  unsigned long linear_servo_setup_time = 2000; // including time to move to far pos
  unsigned long pre_servo_wait = 0; //2000;
  bool terminate_on_error = 1; //0; // end trial as soon as mistake occurs
  unsigned long error_timeout = 1000;
  bool always_reward_r = USE_LEVER;
  unsigned int servo_throw = 0;
} session_params;

// Stimuli
#ifdef SIX_STIM
struct STIMULI_TYPE
{
  static const int N = 6; // number of positions
  const int POSITIONS[N] = {0, 33, 67, 100, 133, 167}; // array of locations to move to
  static const int ROTATION_SPEED = 30; // how fast to rotate stepper
  static const int FIRST_ROTATION = 85;
  
  // wherever the motor starts will be defined as this position
  static const int ASSUMED_INITIAL_POSITION = 0; 
} STIMULI;
#endif

#ifndef SIX_STIM
#ifdef FOUR_STIM
// If not SIX and FOUR
struct STIMULI_TYPE
{
  static const int N = 4; // number of positions
  const int POSITIONS[N] = {0, 50, 100, 150}; // array of locations to move to
  static const int ROTATION_SPEED = 30; // how fast to rotate stepper
  static const int FIRST_ROTATION = 75;
  
  // wherever the motor starts will be defined as this position
  static const int ASSUMED_INITIAL_POSITION = 0; 
} STIMULI;
#endif

#ifndef FOUR_STIM
// If not SIX and not FOUR
struct STIMULI_TYPE
{
  static const int N = 2; // number of positions
  const int POSITIONS[N] = {50, 150}; // array of locations to move to
  static const int ROTATION_SPEED = 60; // how fast to rotate stepper
  static const int FIRST_ROTATION = 50;
  
  // wherever the motor starts will be defined as this position
  static const int ASSUMED_INITIAL_POSITION = 50; 
} STIMULI;
#endif
#endif


// initial position of stim arm .. user must ensure this is correct
int stim_arm_position = STIMULI.ASSUMED_INITIAL_POSITION;

// Debugging announcements
unsigned long speak_at = 1000;
unsigned long interval = 1000;

// State machine timers
unsigned long reward_timer = 0;
unsigned long iti_timer = 0;
unsigned long timer = 0; // generic timer
unsigned int error_flag = 0; // hack for error timeout

// max rewards
unsigned int rewards_this_trial = 0;
unsigned int max_rewards_per_trial = 2;

// touched monitor
uint16_t sticky_touched = 0;

// Servo
Servo linServo;

// Stepper
// 200 steps per rotation; the rest are pin numbers
// overwrite this later in the two-pin case
Stepper stimStepper(200, 8, 9, 10, 11);

//// Function prototypes and default arguments
void rotate_motor(int rotation, unsigned int delay_ms=100);
int set_session_params(SESSION_PARAMS_TYPE &session_params, String cmd);

void setup()
{
  Serial.begin(115200);
  Serial.println("Running setup.");

  // MPR121 touch sensor setup
  pinMode(PINS.TOUCH_IRQ, INPUT);
  digitalWrite(PINS.TOUCH_IRQ, HIGH); //enable pullup resistor
  Wire.begin();
  mpr121_setup(PINS.TOUCH_IRQ);
  
  
  // output pins
  pinMode(5, OUTPUT);
  pinMode(6, OUTPUT);
  pinMode(7, OUTPUT);
  pinMode(8, OUTPUT);
  pinMode(9, OUTPUT);
  pinMode(10, OUTPUT);
  pinMode(11, OUTPUT);
  pinMode(12, OUTPUT);

  if (TWO_PIN_STEPPER)
  {
    stimStepper = Stepper(200, PINS.TWOPIN_STEPPER_1, PINS.TWOPIN_STEPPER_2);
    pinMode(PINS.TWOPIN_ENABLE_STEPPER, OUTPUT);
    digitalWrite(PINS.TWOPIN_ENABLE_STEPPER, LOW); // # Make sure it's off    
  }
  else
  {
    pinMode(PINS.ENABLE_STEPPER, OUTPUT);
    digitalWrite(PINS.ENABLE_STEPPER, LOW); // # Make sure it's off
  }

  // stepper setup
  stimStepper.setSpeed(STIMULI.ROTATION_SPEED);  
    
  // linear servo setup
  linServo.attach(PINS.LINEAR_SERVO);
  linServo.write(SERVO_POSITIONS.FAR);
  delay(session_params.linear_servo_setup_time);

  // random number seed
  randomSeed(analogRead(3));


  
  
}

void loop()
{
  unsigned long time = millis();
  STATE_TYPE next_state = current_state;
  uint16_t touched = 0;

  // Announce the time
  if (time > speak_at)
  {
    Serial.println((String) "DEBUG time " + time);
    speak_at += interval;
  }

  // Receive any chat
  String received_chat;
  received_chat = receive_chat();
  
  // Set session variables
  int status = 0;
  if (received_chat.length() > 0)
    status = set_session_params(session_params, received_chat);
  if (status == 1)
    Serial.println((String) "DEBUG cannot parse " + received_chat);
  
  // for rotating
  int new_position = 0;
  
  // Poll touch inputs
  if (USE_LEVER)
    touched = pollLeverInputs();  
  else
    touched = pollTouchInputs();
  
  // announce sticky
  if (touched != sticky_touched)
  {
    Serial.println((String) time + " EVENT TOUCHED " + touched);
    sticky_touched = touched;
  }  
  
  // state
  switch (current_state)
  {
    case TRIAL_START:
      // Set trial variables
      switch (session_params.force)
      {
        case 'L':
          current_trial_params.rewarded_side = 'L';
          current_trial_params.stim_number = 0;
          break;
        case 'R':
          current_trial_params.rewarded_side = 'R';
          current_trial_params.stim_number = 1;
          break;
        case 'X':
          // choose randomly -- ultimately want to get this from user
          current_trial_params.stim_number = random(0, STIMULI.N);
          
          // use the logic that even stimuli correspond to going left
          // this should come from user to be more robust
          if (current_trial_params.stim_number % 2 == 0)
            current_trial_params.rewarded_side = 'L';
          else
            current_trial_params.rewarded_side = 'R';
          
          break;
      }
      
      current_trial_params.outcome = "current"; // until proven otherwise
      current_trial_params.choice = "nogo"; // until proven otherwise
      
      // where to put servo to
      current_trial_params.servo_position = SERVO_POSITIONS.NEAR +
        SERVO_POSITIONS.POS_DELTA*random(0, session_params.servo_throw);

      // safety
      if (current_trial_params.servo_position > SERVO_POSITIONS.FAR)
        current_trial_params.servo_position = SERVO_POSITIONS.FAR;
      if (current_trial_params.servo_position < SERVO_POSITIONS.NEAR)
        current_trial_params.servo_position = SERVO_POSITIONS.NEAR;

      // Trial start
      Serial.println((String) "TRIAL START " + time);
      Serial.println((String) "TRIAL SIDE " + 
        current_trial_params.rewarded_side);
      Serial.println((String) "TRIAL SERVO_POS " + 
        current_trial_params.servo_position);
      Serial.println((String) "TRIAL STIM_NUMBER " + 
        current_trial_params.stim_number);
      
      // keep track of how many rewards
      rewards_this_trial = 0;
      
      // Set next state
      next_state = MOVE_SERVO_START;
      break;
      
    
    case MOVE_SERVO_START:
      /* Start moving servo to move stimulus into position 
      */
      // current stimulus angle comes from indexing into POSITIONS
      new_position = STIMULI.POSITIONS[current_trial_params.stim_number];

      // rotate it
      rotateStim(new_position);

      // TODO: get rid of this
      delay(.2);
      
      // set position
      linServo.write(current_trial_params.servo_position);
            
      // set timer
      timer = time + SERVO_POSITIONS.NEAR2FAR_TRAVEL_TIME;
    
      // wait state
      next_state = MOVE_SERVO_WAIT;
    
    case MOVE_SERVO_WAIT:
      /* Wait for servo to reach whisking position
      */
    
      // repeatedly set position??
      linServo.write(current_trial_params.servo_position);

      
      // check time
      if (time >= timer)
      {
        next_state = RESPONSE_WINDOW_START;
      }
      break;

    case RESPONSE_WINDOW_START:
      /* Start response window timer
      */
      timer = time + session_params.response_window_dur;
      //Serial.println((String) "DEBUG respons window timer " + timer);
      next_state = RESPONSE_WINDOW;
      break;
      
    case RESPONSE_WINDOW:
      /* Wait for response lick
      */
    
      // transition if response window over
      if (time >= timer)
      {
        next_state = PRE_SERVO_WAIT;
        break;
      }
    
      // transition if max rewards reached
      if (rewards_this_trial >= max_rewards_per_trial)
      {
        next_state = PRE_SERVO_WAIT;
        break;
      }
      
      // Check chat
      if (received_chat.length() > 0)
      {
        received_chat.trim();
      }      

      // What we do depends on which side is rewarded
      switch (current_trial_params.rewarded_side)
      {
        case 'L':
          // transition if received REWARD or touched
          if (received_chat.equals("REWARD"))
          {
            if (session_params.always_reward_r)
              next_state = REWARD_R;
            else
              next_state = REWARD_L;
          }
          
          // correct response
          if ((get_touched_channel(touched, 0) == 1) && 
              (get_touched_channel(touched, 1) == 0))
          {
            // Only store this info for the first choice of the trial
            if (current_trial_params.outcome.equals("current"))
            {
              current_trial_params.outcome = "hit";
              current_trial_params.choice = "go L";
            }
            
            if (session_params.always_reward_r)
              next_state = REWARD_R;
            else
              next_state = REWARD_L;
          }
          
          // incorrect response
          if ((get_touched_channel(touched, 0) == 0) && 
              (get_touched_channel(touched, 1) == 1))
          {
            // Only store this info for the first choice of the trial
            if (current_trial_params.outcome.equals("current"))
            {
              current_trial_params.outcome = "error";
              current_trial_params.choice = "go R";
            }
            
            // end trial if terminate_on_error
            if (session_params.terminate_on_error)
                next_state = ERROR;
          }               
          
          break;
        
        case 'R':
          // transition if received REWARD or touched
          if (received_chat.equals("REWARD"))
          {
            next_state = REWARD_R;
          }
          
          // correct response
          if ((get_touched_channel(touched, 0) == 0) && 
              (get_touched_channel(touched, 1) == 1))
          {
            // Only store this info for the first choice of the trial
            if (current_trial_params.outcome.equals("current"))
            {
              current_trial_params.outcome = "hit";
              current_trial_params.choice = "go R";
            }
            next_state = REWARD_R;
          }
          
          // incorrect response
          if ((get_touched_channel(touched, 0) == 1) && 
              (get_touched_channel(touched, 1) == 0))
          {
            // Only store this info for the first choice of the trial
            if (current_trial_params.outcome.equals("current"))
            {            
              current_trial_params.outcome = "error";
              current_trial_params.choice = "go L";
            }
            
            // end trial if terminate_on_error
            if (session_params.terminate_on_error)
                next_state = ERROR;
          }          
          break;
      }
      break;
          
    case REWARD_L:
      // Rewarding state
      // Chats and touches are ignored!
      // start a timer
      Serial.println((String) time + " EVENT REWARD_L");
      reward_timer = time + session_params.reward_dur_l;
      // rewarding
      digitalWrite(6, HIGH);    // open solenoid valve
    
      // transition
      next_state = REWARD_TIMER_L;
    
      // count rewards
      rewards_this_trial++;
      break;

    case REWARD_R:
      // Rewarding state
      // Chats and touches are ignored!
      // start a timer
      Serial.println((String) time + " EVENT REWARD_R");
      reward_timer = time + session_params.reward_dur_r;
    
      // rewarding
      digitalWrite(7, HIGH);    // open solenoid valve
    
      // transition
      next_state = REWARD_TIMER_R;
    
      // count rewards
      rewards_this_trial++;
      break;
    
    case REWARD_TIMER_L:
      // Waiting state
      // Chats and touches are ignored!
      // wait for timer
      if (time >= reward_timer)
      {
        next_state = POST_REWARD_TIMER_START;
        digitalWrite(6, LOW);
      }
      break;

    case REWARD_TIMER_R:
      // Waiting state
      // Chats and touches are ignored!
      // wait for timer
      if (time >= reward_timer)
      {
        next_state = POST_REWARD_TIMER_START;
        digitalWrite(7, LOW);
      }
      break;
    
    case POST_REWARD_TIMER_START:
      reward_timer = time + session_params.inter_reward_interval;
      next_state = POST_REWARD_TIMER_WAIT;
      break;
    
    case POST_REWARD_TIMER_WAIT:
      if ((time >= reward_timer) && (touched == 0))
        next_state = RESPONSE_WINDOW;
      break;
    
    case ERROR:
      /* An error was made
      We could punish with a timeout or alarm soundhere.
      */
      
      // Announce
      Serial.println((String) time + " EVENT ERROR");
    
      // Hack, we increase the ITI on errors
      error_flag = 1;
    
      next_state = PRE_SERVO_WAIT;
      break;
    
    case PRE_SERVO_WAIT:
      iti_timer = time + session_params.pre_servo_wait;
      next_state = SERVO_WAIT;
      break;
    
    case SERVO_WAIT:
      if (time >= iti_timer)
      {
        next_state = START_INTER_TRIAL_INTERVAL;
      }
      break;
    
    case START_INTER_TRIAL_INTERVAL:
      iti_timer = time + session_params.inter_trial_interval;
    
      if (error_flag)
      {
        iti_timer += session_params.error_timeout;
      }
      error_flag = 0;

      // move stim back
      linServo.write(SERVO_POSITIONS.FAR);
    
      // did nothing happen?
      if (current_trial_params.outcome.equals("current"))
        current_trial_params.outcome = "spoil";
    
      // announce result
      Serial.println((String) "TRIAL OUTCOME " + current_trial_params.outcome);

      next_state = INTER_TRIAL_INTERVAL;
      break;
    
    case INTER_TRIAL_INTERVAL:
      // repeatedly set position?
      linServo.write(SERVO_POSITIONS.FAR);

    
      if (time >= iti_timer)
      {
        next_state = TRIAL_START;
      }
      
      // Check chat
      if (received_chat.length() > 0)
      {
        received_chat.trim();
      }      

      if (received_chat.equals("REWARD L"))
      {
        Serial.println("EVENT MANUAL L");
        digitalWrite(6, HIGH);
        delay(session_params.reward_dur_l);
        digitalWrite(6, LOW);
      }
      else if (received_chat.equals("REWARD R"))
      {
        Serial.println("EVENT MANUAL R");
        digitalWrite(7, HIGH);
        delay(session_params.reward_dur_l);
        digitalWrite(7, LOW);      
      }
      
      break;
  }
  
  // state transition?
  if (next_state != current_state)
  {
    Serial.println(time + (String) " STATE CHANGE " + current_state + " " + next_state);
    current_state = next_state;
  }
}


int get_touched_channel(uint16_t touched, unsigned int i)
{
  return (touched & (1 << i)) >> i;
}

int set_session_params(SESSION_PARAMS_TYPE &session_params, String cmd)
{ /* Update the trial parameters with user requests 
  
  Returns 1 if cannot parse command
  */
  int status = 0;
  
  //~ int i1, i2;
  //~ i1 = 0;
  //~ i2 = cmd.indexOf(' ');
  //~ Serial.println(i1);
  //~ Serial.println(i2);
  //~ return 0;
  //~ Serial.println(cmd.substring(i1, i2));


  char *pch;
  char cmd_carr[cmd.length() + 1];
  cmd.toCharArray(cmd_carr, cmd.length() + 1);
  pch = strtok(cmd_carr, " ");
  char *strs[3];
  int n_strs = 0;
  String s;
  
  // Convert to array of strings
  while (pch != NULL)
  {
    strs[n_strs] = pch;
    n_strs++;
    pch = strtok(NULL, " ");
  }
  
  if ((n_strs == 2) && (strcmp(strs[0], "FORCE") == 0))
  {
    session_params.force = strs[1][0];
  }
  if ((n_strs == 3) && (strcmp(strs[0], "SET") == 0))
  {
    if (strcmp(strs[1], "REWARD_DUR_L") == 0)
    {
      s = strs[2];
      session_params.reward_dur_l = s.toInt();
    }
    else if (strcmp(strs[1], "REWARD_DUR_R") == 0)
    {
      s = strs[2];
      session_params.reward_dur_r = s.toInt();
    }    
    else if (strcmp(strs[1], "MRT") == 0)
    {
      s = strs[2];
      max_rewards_per_trial = s.toInt();
    }
    else if (strcmp(strs[1], "TOE") == 0)
    {
      s = strs[2];
      session_params.terminate_on_error = s.toInt();
    }
    else if (strcmp(strs[1], "PSW") == 0)
    {
      s = strs[2];
      session_params.pre_servo_wait = s.toInt();
    }
    else if (strcmp(strs[1], "TO") == 0)
    {
      s = strs[2];
      session_params.error_timeout = s.toInt();
    }
    else if (strcmp(strs[1], "ST") == 0)
    {
      s = strs[2];
      session_params.servo_throw = s.toInt();
    }
    else if (strcmp(strs[1], "PD") == 0)
    {
      s = strs[2];
      SERVO_POSITIONS.POS_DELTA = s.toInt();
    }
    
  }
  return 0;
  

  

  
  return status;
}   


/* Stepper rotation functions */

void rotateStim(int new_position) 
{ /*
  The distance to move, even if zero, is split into two amounts.
  Positive rotations correspond to CW rotations.
  */
  
  // Determine how far we need to rotate (can be + or -)
  int necessary_rotation = new_position - stim_arm_position;
  
  // Split into two rotations to control for the sound
  int rotation1 = STIMULI.FIRST_ROTATION;
  
  // +ve rotation
  int rotation2 = (necessary_rotation - rotation1 + 200) % 200;
  
  // turn >1/2 rot into a rot the other way
  if (rotation2 > 100) rotation2 -= 200;
  
  // do the rotations
  rotate_motor(rotation1);
  rotate_motor(rotation2);

  // Debugging
  /*
  Serial.print("Rotating stim: old ");
  Serial.print(stim_arm_position);
  Serial.print(" new ");
  Serial.print(new_position);
  Serial.print(" diff ");
  Serial.println(necessary_rotation);
  */
  
  // Return the new, now current, position
  stim_arm_position = new_position;
  //return new_position;
}

void rotate_motor(int rotation, unsigned int delay_ms)
{ /* Low-level rotation function.
  Enables the motor, waits, performs rotation, disables motor.
  Is the wait necessary to ensure it is active???
  Disabling prevents the circuitry from overheating.
  
  I *think* it's necessary to wait after disabling .. a few times
  it kept going forever without this statement.
  */
  bool local_debug = 0;
  
  if (local_debug) Serial.println("Rotating motor");
  if (local_debug) Serial.println("* Enabling");
  if (TWO_PIN_STEPPER)
    digitalWrite(PINS.TWOPIN_ENABLE_STEPPER, HIGH);
  else
    digitalWrite(PINS.ENABLE_STEPPER, HIGH);
  
  if (local_debug) Serial.println("* Delaying");
  delay(delay_ms);
  
  if (local_debug) Serial.println("* Rotating");
  stimStepper.step(rotation);
  
  if (local_debug) Serial.println("* Delaying");
  delay(delay_ms);
  
  if (local_debug) Serial.println("* Disabling");
  if (TWO_PIN_STEPPER)
    digitalWrite(PINS.TWOPIN_ENABLE_STEPPER, LOW);
  else
    digitalWrite(PINS.ENABLE_STEPPER, LOW);  
  
  if (local_debug) Serial.println("* Delaying");
  delay(delay_ms);
  
  if (local_debug) Serial.println("* Finished");
  return;
}

uint16_t pollLeverInputs()
{
  uint16_t res = 0;
  int voltage = 0;
  
  voltage = analogRead(1);
  if (voltage > 512)
    res += 1;
  
  voltage = analogRead(2);
  if (voltage > 512)
    res += 2;
  
  return res;
}
  
