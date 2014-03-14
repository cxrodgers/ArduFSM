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
struct STATE_TYPE
{
  static const int TRIAL_ANNOUNCE = 0;
  static const int WAIT = 1;
  static const int REWARD = 2;
  static const int INTER_TRIAL = 3;
} STATES;


// Debugging announcements
unsigned long speak_at = 1000;
unsigned long interval = 1000;

// State machine global
unsigned int current_state = 0;

// State machine timers
unsigned long reward_timer = 0;


void setup()
{
  Serial.begin(9600);
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
  int next_state = current_state;
  uint16_t touched = 0;

  // Announce the time
  if (time > speak_at)
  {
    Serial.println((String) "DEBUG The time is " + time);
    speak_at += interval;
  }

  // Receive any chat
  String received_chat;
  received_chat = receive_chat();

  // state
  switch (current_state)
  {
    case 0:
      // Trial start
      Serial.println((String) "TRIAL START " + time);
      next_state = 1;
      break;
    
    case 1:
      // Poll touch inputs
      touched = pollTouchInputs();
    
      // Check chat
      if (received_chat.length() > 0)
      {
        received_chat.trim();
      }      

      // transition if received REWARD or touched
      if (received_chat.equals("REWARD") || (touched > 0))
      {
        if (touched > 0)
          Serial.println("TRIAL OUTCOME HIT");
        else
          Serial.println("TRIAL OUTCOME SPOIL");
        next_state = 2;
      }      
      break;
      
    case 2:
      // Rewarding state
      // Chats and touches are ignored!
      // start a timer
      Serial.println((String) "REWARD DELIVERED " + time);
      reward_timer = time + 40;
    
      // rewarding
      digitalWrite(6, HIGH);    // open solenoid valve
    
      // transition
      next_state = 3;
      break;
    
    case 3:
      // Waiting state
      // Chats and touches are ignored!
      // wait for timer
      if (time >= reward_timer)
      {
        next_state = 0;
        digitalWrite(6, LOW);
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
