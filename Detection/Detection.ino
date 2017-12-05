/*
Detection task (1 stim, placed below whiskers). Uses stepper motor
Rewritten from Clay's program for learning arduino.
To be used with optostim.
*/

 
#include "hwconstants.h"


// constants that frequently change:
const int rewSolDur = 35 ; //how long solenoid valve should open to deliver water reward
const int stimCW = 50;
const int stimCCW = -50;
int rewStimFreq = 50;
int ITI = 1000;
int stimDuration = 1500; // how long stimulus should be available for sampling
const int optoStartTime = 00000; // how long to wait before starting laser trials
const int optoStimFreq = 35;
const int stimHoldDelay = 100;


// set up stepper motor
#include <Stepper.h>
Stepper stimStepper(stepsPerRevolution, motorPin1, motorPin2);

// define variables that will change:


int hallThresh = 700;
int hallSensValue = 0;          // variable for reading the hall sensor status
int levPressThreshold = 500; // how long lever has to be held to start
int elapTime = 0;
int leverState = 0;
int prevLevState = 0;
int levPressDur = 0;
int levPressTime = 0;
int levLiftDur = 0;
int startLevLiftCheck = 0;
int rew = 0;
int randSound = 0; // random noise for white noise audio stimuluspu
int drinkDur = 1000; // drink duration
int rewToneDur = 500; // reward tone duration
int unrewTO = 6000; // punishment timeout duration
int liftLevThresh = 100; // how long lever has to be lifted to count as response.
int optoStart =0;
int optoRand = 0;
//int fiberPos = 0;
//int hallSensValue2 = 0;
int stimType = 1; //currently set always to reward

//////////// initialize time variables
long time = 0;
long currentTime=0;
long trigTime = 0;
long levLiftTime = 0;
long randNumber = 0;    // random number for whisker stimulus


void setup() {
  // initialize the LED pin as an output:
  pinMode(startPin, OUTPUT);
  pinMode(optoPin, OUTPUT);
  pinMode(enablePin, OUTPUT); //enable for motor
  pinMode(leverPin, INPUT);
  pinMode(rewPin, OUTPUT);
  pinMode(speakerPin, OUTPUT);
  pinMode(__HWCONSTANTS_H_BACK_LIGHT, OUTPUT);
  digitalWrite(__HWCONSTANTS_H_BACK_LIGHT, HIGH);
  stimStepper.setSpeed(80); 
  Serial.begin(9600);    // initialize serial for output to Processing sketch
  randomSeed(analogRead(2));
  Serial.println("rewarded stimulus frequency = ");
  Serial.println(rewStimFreq);
//  Serial.println("contigTrial = ");
//  Serial.println(contigTrial);
  Serial.println("reward amount/duration =");
  Serial.println(rewSolDur);
  Serial.println("Trial Length (stimDur) =");
  Serial.println(stimDuration);
  Serial.println("ITI =");
  Serial.println(ITI);
  Serial.println("optoStartTime =");
  Serial.println(optoStartTime);
  Serial.println("Session START");
  Serial.println("BEGIN DATA");
}


void loop(){

 ///////////////////START TRIALS
  time = millis();
    
 //make sure lever is pressed before starting trials.
  if (optoStart == 0){
    time = millis();
    if (time > 300000 ){   //can't use variable for  some reason. use number here 300000 = 5 min
      optoStart = 1;
      Serial.println("begin OPTOSTIM");
      Serial.println(millis());
    }
  }  
    
//    if (prevLevState2 == 1) {
//    // check for lever presses during this round when no stimulus is present
//    levState = digitalRead(leverPin);
    
  leverState = digitalRead(leverPin);
  if (leverState == HIGH){
    if(prevLevState == 0) { // if previously not pressed --as in beginning of session
      levPressTime = millis();
      Serial.println("lever press start:");
      Serial.println(levPressTime);
      prevLevState = 1; // set prevLevState to 1, meaning it's been pressed.
    }
     else{ // if lever was already pressed
      currentTime = millis();
      levPressDur = currentTime - levPressTime; // see how long ago
    }
  }
  else {   // if the lever state is low and lever is not pressed then do nothing
    if (leverState == LOW){
      prevLevState =0;
      levPressDur= 0;
    }
  }
 
 ////////////////// START STIMULUS TRIAL
   if(levPressDur > levPressThreshold){ // start trial is lever is held down long enough
     
     trigTime = millis(); // time of stimulus trigger = used to be trigTime2
//     Serial.println("Stimulus trial start at:");
//     Serial.println(trigTime);
     //delay(10); 
     
     digitalWrite(startPin, HIGH); //signal for ttl pulse to signal start trial
     delay(10);
     
     //fiberPos = analogRead(fiberPosPin); //read the input from matlab about position of manipulator
     //Serial.println("fiber position:" );
     //Serial.println(fiberPos);
     //Serial.println(millis());

     if (optoStart == 1) {  //if opto has started
     optoRand = random(1,100);
     
       if (optoRand <= optoStimFreq){
         digitalWrite(optoPin, HIGH); //sends pin HIGH to trigger TTL
         Serial.println("laser ON");
         Serial.println(millis());
         delay(50); //added 0407
       }
       else{
         
         Serial.println("dark");
         Serial.println(millis());
       }
     }
     
     // present rewarded trials according to the defined reward stim frequency
     randNumber = random(0,100); //pick random number 
     if (randNumber <= rewStimFreq){   //
       stimType = 1; // for rewarded trials
     }
     else{
       stimType = 3; // catch trials
     }

     /////////////FOR STIMULUS TRIALS
     if (stimType == 1){ // stimType1 means stimulus and reward trials
       Serial.println("stimulus trial: bottom rewarded");
       Serial.println(millis());
  
      // read the state of the hall effect sensor (for troubleshooting
      digitalWrite(enablePin, HIGH);
      delay(100);
      hallSensValue = analogRead(hallPin);
      leverState = digitalRead(leverPin);
      //~ if (leverState == HIGH) { // if lever is pressed for defined amount of time
        while (hallSensValue < hallThresh){ //rotate motor until it hits the hall effect sensor
          stimStepper.step(-1);
          delay(1);
          hallSensValue = analogRead(hallPin);
          //delay(stimHoldDelay); // hold in position for short period 
  
        } // END of while
      //~ } //END of IF lever press check
      delay(100);
      
      elapTime = 0;
      prevLevState = 0;
      levPressDur = 0;
      startLevLiftCheck = 0;
      
      //reward when lever is lifted
      while (elapTime <= stimDuration){
        time = millis();
        elapTime = time - trigTime;
        leverState = digitalRead(leverPin); 
          if (leverState == HIGH) { // if the lever is pressed start checking for lever lifts.
           startLevLiftCheck = 1;
          }           
          if (startLevLiftCheck == 1) {
            // see how long animal lifts his paw off the lever during stim presentation
            if (leverState == LOW) {   
              // Lever is up
              if (prevLevState == 1) {
                // Lever was previously down and just went up
                // Store lever lift time as now
                levLiftTime = millis();
                prevLevState = 0;
              }
              else {
                // Lever was already up and is still up
                // Recalculate duration
                levLiftDur = millis() - levLiftTime;
              }
            }
            else {
              // Lever is down
              prevLevState = 1;
              levLiftDur = 0;
            }
            //Serial.println(levPressDur);
            
            // trigger REWARD if animal lifts paw during rewarded stim. (for long enough)
            if (levLiftDur >= liftLevThresh) {
                 digitalWrite(optoPin, LOW);
                 digitalWrite(startPin, LOW); // turn off start pin at end of trial to trigger matlab
              reward(); /////////////////// call reward function and print REWARD!!!!!
            }
          }  // end IF for levPressDur > 100 (REWARD sequence)
         
      } // end WHILE elapTime <= stimDur (check for lever lifts)
      digitalWrite(optoPin, LOW);
      digitalWrite(startPin, LOW); // turn off start pin at end of trial to trigger matlab
      
      
      // MOVE STIM BACK
      stimStepper.step(stimCW); // 042110: now using Stepper library for stim control (+ is clockwise)
      delay(200);
      digitalWrite(enablePin, LOW);

      prevLevState = 0;   // reset state variable to allow for consecutive triggers
      //prevType = 1; // for stimCount to promote alternation
     } // END of if stimType = 1 (rewarded trial)
     
     
     //////////////////////////////////catch trials
     
     else{
       Serial.println("catch trial");
       Serial.println(millis());
       
       //no hall effect sensor - just move it away.
       digitalWrite (enablePin, HIGH);
       delay(100);
       stimStepper.step(stimCW);
             
       // check if mouse lifts lever during catch trial
       elapTime = 0;
       prevLevState = 0;
       levPressDur = 0;
       
       // bug here where startLevLiftCheck is not set to zero, so uses
       // its previous value
       // Thus, if the animal lifted his paw while the motor is moving,
       // it will not count as a release on GO trials, but it may count
       // as a release on NOGO trials (if startLevLiftCheck was still set to
       // 1 from the previous trial).
       
       while (elapTime <= stimDuration) {
         time = millis();
         elapTime = time - trigTime; 
         leverState = digitalRead(leverPin);
         if (leverState == HIGH){ // if the lever is pressed start checking for lever lifts.
           startLevLiftCheck = 1;
         }
         if (startLevLiftCheck ==1){ //if the lever is already pressed 
           if(leverState == LOW){
             if(prevLevState ==1){
               levLiftTime = millis();
               prevLevState = 0;
             }
             else{
               levLiftDur = millis()-levLiftTime;
             }
           }
         else{
             prevLevState = 1;
             levLiftDur = 0;
           }
           
         if (levLiftDur >= liftLevThresh){ // if lever lifted during catch trial.
            digitalWrite(optoPin, LOW);
             digitalWrite(startPin, LOW); // turn off start pin at end of trial to trigger matlab
         punish();
           }
        }
       } // END while loop 
          digitalWrite(optoPin, LOW);
          digitalWrite(startPin, LOW); // turn off start pin at end of trial to trigger matlab
      //  move stimback to rest position
      stimStepper.step(stimCCW);
      delay(200);
       
       // digitalWrite(optoPin, LOW);
       
       prevLevState = 0;  //reset state variable for consecutive triggers
     }// END else 
     
    
     //endTime = millis(); 
     
     delay(ITI); //inter-trial interval    

     // Pulse the back light
     Serial.println("end of trial");
     Serial.println(millis());
     digitalWrite(__HWCONSTANTS_H_BACK_LIGHT, LOW);
     delay(25);
     digitalWrite(__HWCONSTANTS_H_BACK_LIGHT, HIGH);   
     
   } 
    // END of if (levPressDur > levPresThresh)
} // END of loop
   
   
   
   
   
//
//////////////////////////////////////////////////////////////////////
///////Define functions:
void reward() { // print "REWARD!!!" play cue tone, open and close valve.
   //
    Serial.println("REWARD!!!");
    Serial.println(millis());

    // REWARD SEQUENCE
    // go through reward/optouum solenoid sequence
    digitalWrite(rewPin, HIGH);    // open solenoid valve for a short time
    delay(rewSolDur);                  // 8ms ~= 8uL of reward liquid (on box #4 011811)
    digitalWrite(rewPin, LOW);

    // PLAY TONE
    rew = 1;
    cueTone();
    delay(drinkDur);
    elapTime = stimDuration + 1;  // break out of the reward stimulus loop after receiving reward
   
} // END of reward function

void punish() {
//  digitalWrite(vacPin, HIGH);    // send output signal for punishment to record analog timing 
//  delay(50);                  // 
//  digitalWrite(vacPin, LOW);

  //digitalWrite(airpuffPin, HIGH);    // give aversive light for wrong press
  Serial.println("unrewarded punishment");
  Serial.println(millis());
  delay(10);  // changed this from 2000 because air puff goes on falling phase
  
    rew = 0;
    cueTone();
    delay(10);
  elapTime = stimDuration + 1;  // 091311: need to check and make sure "elapTime1&2" are not in conflict
} // END of punish function

void cueTone() {  
  // Bug, this overlaps with the global used for elapsed trial time
  // But elapTime is overwritten in reward() and punish() so it's okay
  trigTime = millis();  
   if (rew == 1) {  // if its a reward tone
    while ((time-trigTime) < rewToneDur) {
      digitalWrite(speakerPin, HIGH);
      delayMicroseconds(100);
      digitalWrite(speakerPin, LOW); 
      delayMicroseconds(1);
      time = millis();
     }
   }
   else {  // if its a punishment tone (white noise)
      while ((time-trigTime) < unrewTO) {
        randSound = random(50,700);
        digitalWrite(speakerPin, HIGH);
        delayMicroseconds(randSound);
        digitalWrite(speakerPin, LOW); 
        delayMicroseconds(randSound);
        time = millis();
      }
     }    
} // END cueTone function
   
