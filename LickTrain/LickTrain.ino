#include "chat.h"
#include "mpr121.h"
#include <Wire.h> # also for mpr121

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
  WAIT_L,
  WAIT_R,
  REWARD_L,
  REWARD_R,
  REWARD_TIMER_L,
  REWARD_TIMER_R,
  START_INTER_TRIAL_INTERVAL,
  INTER_TRIAL_INTERVAL
} current_state = TRIAL_START;

// Trial variables
struct TRIAL_PARAMS_TYPE
{
  char rewarded_side = 'L';
} current_trial_params;

// Session params -- combine this with trial variables
struct SESSION_PARAMS_TYPE
{
  char force = 'X';
  unsigned long inter_trial_interval = 1000;
  unsigned long reward_dur_l = 27; // 27 for L1
  unsigned long reward_dur_r = 38; // 38 for L1
} session_params;

// Debugging announcements
unsigned long speak_at = 1000;
unsigned long interval = 1000;

// State machine timers
unsigned long reward_timer = 0;
unsigned long iti_timer = 0;

// touched monitor
uint16_t sticky_touched = 0;


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

      // Trial start
      Serial.println((String) "TRIAL START " + time);
      Serial.println((String) "TRIAL SIDE " + 
        current_trial_params.rewarded_side);
    
      // Set next state
      switch (current_trial_params.rewarded_side)
      {
        case 'L':
          next_state = WAIT_L;
          break;
        case 'R':
          next_state = WAIT_R;
          break;
      }

      break;
    
    case WAIT_L:
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

      // transition if received REWARD or touched
      if (received_chat.equals("REWARD"))
      {
        Serial.println("TRIAL OUTCOME SPOIL");
        next_state = REWARD_L;
      }
      
      if ((get_touched_channel(touched, 0) == 1) && 
          (get_touched_channel(touched, 1) == 0))
      {
        Serial.println("TRIAL OUTCOME HIT");
        //~ Serial.println((String) "DEBUG touched = " + (String) touched);
        next_state = REWARD_L;
      }
      break;

    case WAIT_R:
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

      // transition if received REWARD or touched
      if (received_chat.equals("REWARD"))
      {
        Serial.println("TRIAL OUTCOME SPOIL");
        next_state = REWARD_R;
      }
      
      if ((get_touched_channel(touched, 1) == 1) && 
          (get_touched_channel(touched, 0) == 0))
      {
        Serial.println("TRIAL OUTCOME HIT");
        //~ Serial.println((String) "DEBUG touched = " + (String) touched);
        next_state = REWARD_R;
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
        next_state = START_INTER_TRIAL_INTERVAL;
        digitalWrite(6, LOW);
      }
      break;

    case REWARD_TIMER_R:
      // Waiting state
      // Chats and touches are ignored!
      // wait for timer
      if (time >= reward_timer)
      {
        next_state = START_INTER_TRIAL_INTERVAL;
        digitalWrite(7, LOW);
      }
      break;
    
    case START_INTER_TRIAL_INTERVAL:
      iti_timer = time + session_params.inter_trial_interval;
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
