#include "chat.h"
#include "mpr121.h"
#include <Wire.h> # also for mpr121
#include <Servo.h>


// Pins
struct PINS_TYPE 
{
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
  INTER_TRIAL_INTERVAL
} current_state = TRIAL_START;


// Locations of the servo
struct SERVO_POSITIONS_TYPE 
{
  static const int NEAR = 45; // position when within whisking range
  static const int FAR = 55; // position when out of whisking range
  static const unsigned long NEAR2FAR_TRAVEL_TIME = 1500;
} SERVO_POSITIONS;

// Trial variables
struct TRIAL_PARAMS_TYPE
{
  char rewarded_side = 'L';
  String outcome = "spoil";
  String choice = "nogo";
} current_trial_params;

// Session params -- combine this with trial variables
struct SESSION_PARAMS_TYPE
{
  char force = 'X';
  unsigned long inter_trial_interval = 2000; // Ensure this is > NEAR2FAR_TRAVEL_TIME for now
  unsigned long response_window_dur = 6000;
  unsigned long inter_reward_interval = 500; // assuming multiple rewards in response window possible
  unsigned long reward_dur_l = 30;
  unsigned long reward_dur_r = 45;  
  unsigned long linear_servo_setup_time = 2000; // including time to move to far pos
} session_params;

// Debugging announcements
unsigned long speak_at = 1000;
unsigned long interval = 1000;

// State machine timers
unsigned long reward_timer = 0;
unsigned long iti_timer = 0;
unsigned long timer = 0; // generic timer

// touched monitor
uint16_t sticky_touched = 0;

// Servo
Servo linServo;



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

  // linear servo setup
  linServo.attach(PINS.LINEAR_SERVO);
  linServo.write(SERVO_POSITIONS.FAR);
  delay(session_params.linear_servo_setup_time);
  
  
  
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
  int status = set_session_params(session_params, received_chat);
  if (status == 1)
    Serial.println((String) "DEBUG cannot parse " + received_chat);
  

  // state
  switch (current_state)
  {
    case TRIAL_START:
      // Set trial variables
      switch (session_params.force)
      {
        case 'L':
          current_trial_params.rewarded_side = 'L';
          break;
        case 'R':
          current_trial_params.rewarded_side = 'R';
          break;
        case 'X':
          // should choose randomly
          current_trial_params.rewarded_side = 'L';
          break;
      }
      
      current_trial_params.outcome = "spoil"; // until proven otherwise
      current_trial_params.choice = "nogo"; // until proven otherwise

      // Trial start
      Serial.println((String) "TRIAL START " + time);
      Serial.println((String) "TRIAL SIDE " + 
        current_trial_params.rewarded_side);
    
      // Set next state
      next_state = MOVE_SERVO_START;
      break;
      
    
    case MOVE_SERVO_START:
      /* Start moving servo to move stimulus into position 
      */
      // set position
      linServo.write(SERVO_POSITIONS.NEAR);
    
      // would also rotate arm here...
      
      // set timer
      timer = time + SERVO_POSITIONS.NEAR2FAR_TRAVEL_TIME;
    
      // wait state
      next_state = MOVE_SERVO_WAIT;
    
    case MOVE_SERVO_WAIT:
      /* Wait for servo to reach whisking position
      */
      // Poll touch inputs
      touched = pollTouchInputs();
      
      // announce sticky
      if (touched != sticky_touched)
      {
        Serial.println((String) time + " EVENT TOUCHED " + touched);
        sticky_touched = touched;
      }
      
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
        next_state = START_INTER_TRIAL_INTERVAL;
      }
    
      // Poll touch inputs
      touched = pollTouchInputs();
      
      // announce sticky
      if (touched != sticky_touched)
      {
        Serial.println((String) time + " EVENT TOUCHED " + touched);
        sticky_touched = touched;
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
            next_state = REWARD_L;
          }
          
          if ((get_touched_channel(touched, 0) == 1) && 
              (get_touched_channel(touched, 1) == 0))
          {
            current_trial_params.outcome = "hit";
            current_trial_params.choice = "go L";
            next_state = REWARD_L;
          }
          break;
        
        case 'R':
          // transition if received REWARD or touched
          if (received_chat.equals("REWARD"))
          {
            next_state = REWARD_R;
          }
          
          if ((get_touched_channel(touched, 0) == 0) && 
              (get_touched_channel(touched, 1) == 1))
          {
            current_trial_params.outcome = "hit";
            current_trial_params.choice = "go R";
            next_state = REWARD_R;
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
      if (time >= reward_timer)
        next_state = RESPONSE_WINDOW;
      break;
    
    case START_INTER_TRIAL_INTERVAL:
      iti_timer = time + session_params.inter_trial_interval;

      // move stim back
      linServo.write(SERVO_POSITIONS.FAR);
    
      // announce result
      Serial.println((String) "TRIAL OUTCOME " + current_trial_params.outcome);

      next_state = INTER_TRIAL_INTERVAL;
      break;
    
    case INTER_TRIAL_INTERVAL:
      if (time >= iti_timer)
      {
        next_state = TRIAL_START;
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
  
  // If sent FORCE L or FORCE R, then set session_params accordingly
  if ((cmd.substring(0, 5) == "FORCE"))
  {
    if (cmd.substring(5, 7) == " L")
    {
      session_params.force = 'L';
    }
    else if (cmd.substring(5, 7) == " R")
    {
      session_params.force = 'R';
    }
    else
    {
      // Cannot parse command
      status = 1;
    }
  }
  
  
  if ((cmd.substring(0, 15) == "SET REWARD_DUR_"))
  {
    if (cmd.substring(15, 16) == "L")
    {
      session_params.reward_dur_l = cmd.substring(17).toInt();
    }
    else if (cmd.substring(15, 16) == "R")
    {
      session_params.reward_dur_r = cmd.substring(17).toInt();
    }
    else
    {
      // Cannot parse command
      status = 1;
    }
  }
  
  return status;
}   