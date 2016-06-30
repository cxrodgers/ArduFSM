/* Last updated DDK 6/7/16
 *  
 * OVERVIEW: 
 * This file defines the state-dependent operations for the ArduFSM protocol 
 * MultiSens.
 * 
 * 
 * REQUIREMENTS:
 * This sketch must be located in the MultiSens protocol directory within
 * a copy of the ArduFSM repository on the local computer's Arduino sketchbook
 * folder. In addition to this file, the MultiSens directory should contain
 * the following files:
 * 
 * 1. States.h
 * 2. MultiSens.ino
 * 
 * In addition, the local computer's Arduino sketchbook library must contain 
 * the following libraries:
 *  
 * 1. chat, available at https://github.com/cxrodgers/ArduFSM/tree/master/libraries/chat
 * 2. TimedState, available at https://github.com/cxrodgers/ArduFSM/tree/master/libraries/TimedState
 * 3. devices, available at https://github.com/danieldkato/devices
 * 
 * 
 * DESCRIPTION:
 * At the heart of this code is a function called stateDependentOperations. This 
 * function is called on every pass of the loop() function in the main .ino file, 
 * which passes it the variable current_state. Nested in the function is a switch 
 * case statement that executes the appropriate block of code based on the FSM's 
 * current state. 
 * 
 * Many of these cases invoke objects that are used for managing task epochs that
 * must be distributed over multiple passes of the main .ino's loop function 
 * because they take more than a few ms, and we want loop to complete as quickly
 * as possible so that we can quickly check for licks again and get any new 
 * messages from the host PC. All of these objects instantiate protocol-specific
 * classes that inherit from TimedState, defined in ArduFSM/libraries. These 
 * TimedState sub-classes are declared in States.h and defined and instantiated 
 * in this file. These TimedState objects store the time the corresponding state 
 * began as well as the current time, and execute appropriate class functions based 
 * on how much time has elapsed since the beginning of the state.
 * 
 * This file also defines arrays that store trial and response parameters for 
 * the current trial.
 */


/* Implementation file for declaring protocol-specific states.
This implements a two-alternative choice task with two lick ports.

Defines the following:
* param_abbrevs, which defines the shorthand for the trial parameters
* param_values, which define the defaults for those parameters
* results_abbrevs, results_values, default_results_values
* implements the state functions and state objects

*/

#include "devices.h"
#include "States.h"
#include "Arduino.h"
#include "Stepper.h"
// include this one just to get __TRIAL_SPEAK_YES
#include "chat.h"

// Make this true to generate random responses for debugging
#define FAKE_RESPONDER 0

extern STATE_TYPE next_state;
extern bool flag_start_trial;

int lickThresh = 900;
int Device::deviceCounter = 0;

// These should go into some kind of Protocol.h or something
char* param_abbrevs[N_TRIAL_PARAMS] = {
  "STPRIDX", "SPKRIDX", "STIMDUR", "REW", "REW_DUR", 
  "IRI", "TO", "ITI", "RWIN", "MRT", 
  "TOE" 
  };
long param_values[N_TRIAL_PARAMS] = {
  0, 0, 2000, 0, 50, 
  500, 6000, 3000, 3000, 1,
  1   
  };

// Whether to report on each trial  
// Currently, manually match this up with Python-side
// Later, maybe make this settable by Python, and default to all True
// Similarly, find out which are required on each trial, and error if they're
// not set. Currently all that are required_ET are also reported_ET.
bool param_report_ET[N_TRIAL_PARAMS] = {
  1, 1, 1, 1, 0, 
  0, 0, 0, 0, 0,
  0
};
  
char* results_abbrevs[N_TRIAL_RESULTS] = {"RESP", "OUTC"};
long results_values[N_TRIAL_RESULTS] = {0, 0};
long default_results_values[N_TRIAL_RESULTS] = {0, 0};


/* Instantiate device objects that will be used for controlling individual 
 * hardware devices like stepper motors, speakers, solenoids, etc. This is an
 * additional layer of complication that is specific to this MultiSens protocol,
 * and may not generalize to other protocols.
 * 
 * In this task, I want the objects managing my hardware to inherit from a 
 * common parent some virtual doStuff function that they can re-define
 * appropriately based on the type of physical device they control (e.g.,
 * extend a stepper for a stepper motor, emit a tone for speaker). Then, all
 * of these objects can be put in an array, and a calling function can iterate 
 * through the array and dereference each element's doStuff function in quick
 * succession, facilitating near-simultaneous control of multiple hardware
 * devices.
 */
Device ** devPtrs = config_hw();
int devIndices[NUM_DEVICES] = { tpidx_STPRIDX, tpidx_SPKRIDX };



/* Instantiate state objects for handling task epochs that should persist over 
 * multiple passes of the main .ino file's loop() function, i.e., last more than 
 * a few ms. While these classes are protocol-specific (defined in this States.cpp 
 * file) they all inherit from TimedState, which is used across protocols and
 * defined in ArduFSM/libraries. 
 * 
 * These objects will be invoked from stateDependentOperations, the function for 
 * deciding how the Arduino should behave based on the current state. 
 */
static StimPeriod stim_period(param_values[tpidx_STIM_DUR]);
static StateResponseWindow srw(param_values[tpidx_RESP_WIN_DUR]);
static StateFakeResponseWindow sfrw(param_values[tpidx_RESP_WIN_DUR]);
static StateInterTrialInterval state_inter_trial_interval(param_values[tpidx_ITI]);
static StateErrorTimeout state_error_timeout(param_values[tpidx_ERROR_TIMEOUT]);
static StatePostRewardPause state_post_reward_pause(param_values[tpidx_INTER_REWARD_INTERVAL]);



/* Define stateDependentOperations, the function for deciding how the Arduino  
 * should behave based on the current state. This gets called from the main 
 * .ino file's loop() function, and will in turn invoke the TimedState objects
 * instantiated above, as well as a number of non-class functions defined below. 
 */
void stateDependentOperations(STATE_TYPE current_state, unsigned long time){
    switch (current_state)
    {
    //// Wait till the trial is released. Same for all protocols.
      case WAIT_TO_START_TRIAL:
        // Wait until we receive permission to continue  
        if (flag_start_trial)
        {
          // Announce that we have ended the trial and reset the flag
          Serial.print(time);
          Serial.println(" TRL_RELEASED");
          flag_start_trial = 0;
        
          // Proceed to next trial
          next_state = TRIAL_START;
        }
        break;

      //// TRIAL_START. Same for all protocols.
      case TRIAL_START:
    
        // Set up the trial based on received trial parameters
        Serial.print(time);
        Serial.println(" TRL_START");
        for(int i=0; i < N_TRIAL_PARAMS; i++)
        {
          if (param_report_ET[i]) 
          {
            // Buffered write would be nice here
            Serial.print(time);
            Serial.print(" TRLP ");
            Serial.print(param_abbrevs[i]);
            Serial.print(" ");
            Serial.println(param_values[i]);
          }
        }
    
        // Set up trial_results to defaults
        for(int i=0; i < N_TRIAL_RESULTS; i++)
        {
          results_values[i] = default_results_values[i];
        }      
    
        next_state = STIM_PERIOD;
        break;

      case STIM_PERIOD:
        stim_period.run(time);
        break;
    
      case RESPONSE_WINDOW:
        if (FAKE_RESPONDER)
        {
          sfrw.update();
          sfrw.run(time);
        } 
        else 
        {
          srw.update();
          srw.run(time);
        }
        break;
    
      case REWARD:
        Serial.print(time);
        Serial.println(" EV R_L");
        state_reward(next_state);
        break;
    
      case POST_REWARD_PAUSE:
        state_post_reward_pause.run(time);
        break;    
    
      case ERROR:
      
        state_error_timeout.run(time);
        break;

      case INTER_TRIAL_INTERVAL:

        // Announce trial_results
        state_inter_trial_interval.run(time);
        break;
    
    // need an else here
  }
}


/* Definitions for the various TimedState sub-classes invoked in 
 * stateDependentOperations. Each of these sub-classes can re-define the virtual 
 * s_setup(), loop(), s_finish() and update() functions they inherit from 
 * TimedState - although they do not need to, as these functions are defined
 * in TimedState as merely virtual rather than pure virtual, meaning that
 * they do already have an implementation in TimedState (they mostly just do 
 * nothing by default). 
 */
 
//StimPeriod definitions:
void StimPeriod::s_setup(){
  duration = param_values[tpidx_STIM_DUR];  
  licked = 0;
  for ( int i = 0; i < NUM_DEVICES; i++ ){
    devFcns[i] = param_values[devIndices[i]]; 
  }
}

void StimPeriod::loop(){
  unsigned long time = millis();
  for ( int i = 0; i < NUM_DEVICES; i++ ){
    devPtrs[i] -> loop(devFcns[i]);
  }
  //on rewarded trials, make reward coterminous with stimulus
  if ( param_values[tpidx_REW] == 1 && (timer - time) < param_values[tpidx_REW_DUR] ){
    digitalWrite(SOLENOID_PIN, HIGH);
  }
}

void StimPeriod::s_finish()
{
  for ( int i = 0; i < NUM_DEVICES; i++ ){
    devPtrs[i] -> s_finish();
  }
  digitalWrite(SOLENOID_PIN, LOW);
  //if the mouse licked during the stimulus period, transition to timeout
  if ( licked == 1 ){ 
    next_state = ERROR; 
  }
  //if not, transition to response window
  else {
    next_state = RESPONSE_WINDOW;
  }
}


// StateResponseWindow definitions:
void StateResponseWindow::update()
{
 my_licking = checkLicks();
}

void StateResponseWindow::s_setup(){
  duration = param_values[tpidx_RESP_WIN_DUR];
}

void StateResponseWindow::loop()
{
  int current_response;
  bool licking;
  // get the licking state 
  // overridden in FakeResponseWindow
  set_licking_variables(licking);
  // transition if max rewards reached
  if (my_rewards_this_trial >= param_values[tpidx_MRT])
  {
    next_state = INTER_TRIAL_INTERVAL;
    flag_stop = 1;
    return;
  }
  // Do nothing if both or neither are being licked.
  // Otherwise, assign current_response.
  if (!licking)
    return;
  else if (licking)
    current_response = GO;
  else
    Serial.println("ERR this should never happen");
  // Only assign result if this is the first response
  if (results_values[tridx_RESPONSE] == 0)
    results_values[tridx_RESPONSE] = current_response;
  // Move to reward state, or error if TOE is set, or otherwise stay
  if ((current_response == GO) && (param_values[tpidx_REW] == GO))
  { // Hit
    next_state = REWARD;
    my_rewards_this_trial++;
    results_values[tridx_OUTCOME] = OUTCOME_HIT;
  }
  else if (param_values[tpidx_TERMINATE_ON_ERR] == __TRIAL_SPEAK_NO)
  { // Error made, TOE is false
    // Decide how to deal with this non-TOE case
  }
  else
  { // Error made, TOE is true
    results_values[tridx_OUTCOME] = OUTCOME_FA;
    next_state = ERROR;
  }
}

void StateResponseWindow::s_finish()
{
  // If response is still not set, mark as a nogo response
  if (results_values[tridx_RESPONSE] == 0)
  {
    // The response was nogo
    results_values[tridx_RESPONSE] = NOGO;
    
    // Outcome depends on what he was supposed to do
    if (param_values[tpidx_REW] == NOGO) {
      // Correctly did nothing on a NOGO trial
      results_values[tridx_OUTCOME] = OUTCOME_CR;
    } else {
      results_values[tridx_OUTCOME] = OUTCOME_MISS;
    }

  // In any case the trial is over
  next_state = INTER_TRIAL_INTERVAL;
  }
}

void StateResponseWindow::set_licking_variables(bool &licking)
{ /* Gets the current licking status from the touched variable for each port */
  
  int aIn = analogRead(LICK_DETECTOR_PIN);
  if ( aIn > lickThresh ){
    licking = 1;
  }
  else {
    licking = 0;
  }
}


// StateFakeResponsewindow definitions:
// Differs only in that it randomly fakes a response
void StateFakeResponseWindow::set_licking_variables(bool &licking)
{ /* Fakes a response by randomly choosing lick status for each */
  licking = (random(0, 10000) < 3);       
}


// Inter-trial interval definitions:
void StateInterTrialInterval::s_setup()
{
  duration = param_values[tpidx_ITI];
  // First-time code: Report results
  for(int i=0; i < N_TRIAL_RESULTS; i++)
  {
    Serial.print(time_of_last_call);
    Serial.print(" TRLR ");
    Serial.print(results_abbrevs[i]);
    Serial.print(" ");
    Serial.println(results_values[i]);
  }
}

void StateInterTrialInterval::s_finish()
{
  next_state = WAIT_TO_START_TRIAL;   
}


// Post-reward state definitions:
void StatePostRewardPause::s_finish()
{
  next_state = RESPONSE_WINDOW;
}


// StateErrorTimeout definitions:
void StateErrorTimeout::s_finish()
{
  next_state = INTER_TRIAL_INTERVAL;
}

void StateErrorTimeout::s_setup(){
  duration = param_values[tpidx_ERROR_TIMEOUT];  
}



/* Definitions for non-class functions for handling states that can be dispatched
 * on a single pass of the main .ino file's main loop() function (i.e., last no
 * more than a few ms). 
 */
int state_reward(STATE_TYPE& next_state)
{
  digitalWrite(SOLENOID_PIN, HIGH);
  delay(param_values[tpidx_REW_DUR]);
  digitalWrite(SOLENOID_PIN, LOW); 
  next_state = POST_REWARD_PAUSE;
  return 0;  
}



/* Utility functions */
boolean checkLicks(){
  boolean licking;
  int aIn = analogRead(LICK_DETECTOR_PIN);
    if ( aIn > lickThresh ){
      licking = 1;
    }
    else {
      licking = 0;
    }
  return licking;
}


Device ** config_hw(){ 
    
    bool debug = 1; // set to 0 if using real hardware devices; set to 1 if using dummy devices
    
    if ( debug == 0 ){
        static myStepper myStp1( NUM_STEPS, STPR1_PIN1, STPR1_PIN1, ENBL1_PIN, HALL1_PIN, HALL1_THRESH, STPR1_SPEED, STPR1_CW, STPR1_CCW, HALL1_VAL );  
        static mySpeaker spkr1( SPKR_PIN );
  
        static Device * devPtrs[] = { &myStp1, &spkr1 };
        return devPtrs;
        }
    else {
        static dummyStepper dmStpr1;
        static dummySpeaker dmSpkr1;
  
        static Device * devPtrs[] = { &dmStpr1, &dmSpkr1 };
        return devPtrs;
    }    
}
