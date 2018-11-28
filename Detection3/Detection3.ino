/*
Detection task (1 stim, placed below whiskers). Uses stepper motor
Rewritten from Clay's program for learning arduino.
To be used with optostim.
*/
// set up behavior parameters that wont' change during session:

String programName = "Detection_sss_longlever.pde" ; 
String notes = "for triggering laser during random trials during Go-nogo detection task";

///////////////////////////////////////////////////
// constants that frequently change:
const int rewSolDur = 45; //how long solenoid valve should open to deliver water reward
int unrewTO = 5000 ;// 3-7000 for well-trained; //  punishment timeout duration
int rewStimFreq =50;
//////////////////////////////////////////////////

int ITI = 500;
int stimDuration = 1800; // how long stimulus should be available for sampling changed from 1.2 to 1 on 4/25/2017
const long optoStartTime = 300000; // how long to wait before starting laser trials
const int optoStimFreq = 50;
// const int stimHoldDelay = 100; //changed from 100 on 170524 not in use
const int stimCW = 30;
const int stimCCW = -30;
// constants won't change. They're used here to set pin numbers:
//PCB board uses transistor-only 2 Digital pins needed 

const int DIR_PIN = 8;  // direction
const int STEP_PIN= 6;  // step pin
const int enablePin = 7;
const int rotation = 200; // # steps for the motor: 200 (full) steps/360deg. 1/4 for microstepping
const int rotationSpeed = 500;// set in microseconds (set #steps/sec)
int x =0 ; // for setting loop for stepper motor

const int startPin = 2; // signals start of trial // triggers matlab
const int optoPin = 13; // used to be vac pin
const int lampPin = 4;
const int hallPin = 1;     // the number of the hall effect sensor pin
const int ledPin =  13; // the number of the LED pin
const int leverPin = 10; //used to be pin 9 on orig OM2 boards
const int rewPin = 5; // solenoid valve pin
const int speakerPin = 11; //speaker pin

//const int fiberPosPin = 4; // analog input from matlab to indicate which position fiber is placed
// set up stepper motor
//#include <Stepper.h>
//Stepper stimStepper(stepsPerRevolution, motorPin1, motorPin2);

// define variables that will change:


int hallThresh = 700;
int hallSensValue = 0;          // variable for reading the hall sensor status
int levPressThreshold = 200; // how long lever has to be held to start
int elapTime = 0;
int leverState = 0;
int prevLevState = 0;
int levPressDur = 0;
int levPressTime = 0;
int levLiftDur = 0;
int startLevLiftCheck = 0;
int rew = 0;
int randSound = 0; // random noise for white noise audio stimuluspu
int drinkDur = 500; // drink duration
int rewToneDur = 500; // reward tone duration
int trialStartTime =0;
int liftLevThresh = 50; // how long lever has to be lifted to count as response. 100 normally
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
long ITIendTime = 0;

void setup() {
  // initialize the LED pin as an output:
  digitalWrite(optoPin,LOW);
  pinMode(startPin, OUTPUT);
  pinMode(optoPin, OUTPUT);
  //pinMode(ledPin, OUTPUT);  
  pinMode(leverPin, INPUT);
  pinMode(rewPin, OUTPUT);
  pinMode(speakerPin, OUTPUT);
  pinMode(speakerPin, OUTPUT);
  
  pinMode(enablePin, OUTPUT); 
  pinMode(STEP_PIN,OUTPUT); // Step
  pinMode(DIR_PIN,OUTPUT); // Dir
  digitalWrite(enablePin,LOW); // Set Enable low
  
  Serial.begin(9600);    // initialize serial for output to Processing sketch
  randomSeed(analogRead(2));
  Serial.println("Program name:");
  Serial.println(programName);
  Serial.println("Notes:");
  Serial.println(notes);
  Serial.println("rewarded stimulus frequency = ");
  Serial.println(rewStimFreq);

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
 ///////////////////START TRIALS: GO OR NOGO?

 //make sure lever is pressed before starting trials.
  if (optoStart == 0){
    time = millis();
    if (time > optoStartTime ){   
      optoStart = 1;
      Serial.println("begin OPTOSTIM");
      Serial.println(millis());
    }
  }  
    
////////////////// START STIMULUS TRIAL: GO OR NOGO
 
  leverState = digitalRead(leverPin); 
  if (leverState == HIGH){ // if lever is pressed
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
  else {   // if the lever is not pressed then do nothing
    if (leverState == LOW){
      prevLevState =0;
      levPressDur= 0;
    }
  }
 
 ////////////////// START STIMULUS TRIAL
   if(levPressDur > levPressThreshold){ // start trial is lever is held down long enough
     
     trigTime = millis(); // time of stimulus trigger = used to be trigTime2
     digitalWrite(lampPin, LOW); //signal for ttl pulse to signal start trial
     delay(25);
     digitalWrite(lampPin, HIGH);
     Serial.println("Trial started at:");
     Serial.println(trigTime); // start counting trial duration
     //delay(10); 
     
     digitalWrite(startPin, HIGH); //signal for ttl pulse to signal start trial
     startTone();   // PLAY TRIAL START TONE
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
         delay(50); //added 040715
       }
       else{
         
         Serial.println("dark");
         Serial.println(millis());
         delay(50); //added 0407
       }
     }
     
     // present rewarded trials according to the defined reward stim frequency
     randNumber = random(1,100); //pick random number 
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
           // hallSensValue = analogRead(hallPin);
           //leverState = digitalRead(leverPin);
           // No need to check lever state again here
           //if (leverState == HIGH) { // if lever is pressed for defined amount of time
          digitalWrite(DIR_PIN,HIGH); // Set Dir high = cw
          for(x = 0; x < rotation; x++){ // Loop 200 times
          digitalWrite(STEP_PIN,HIGH); // Output high
          delayMicroseconds(rotationSpeed); 
          digitalWrite(STEP_PIN,LOW); // Output low
          delayMicroseconds(rotationSpeed);
         } // note: arduino can't do anything else during this period
      delay(50);
      
      elapTime = 0; 
      prevLevState = 0;
      levPressDur = 0;
      startLevLiftCheck = 0;
      
      while (elapTime <= stimDuration){
        currentTime = millis();
        elapTime = currentTime - trigTime;
        leverState = digitalRead(leverPin); 
          if (leverState == HIGH) { // if the lever is pressed start checking for lever lifts.
           startLevLiftCheck = 1;
          }           
          if (startLevLiftCheck == 1) {
                // see how long animal lifts his paw off the lever during stim presentation
            if (leverState == LOW) {   // Lever is lifted
              if (prevLevState == 1) {  //  but was previously pressed                                      
                levLiftTime = millis();  // Store lever lift time as now
                prevLevState = 0;
              }
              else { // if leverstate is 0 (lever lifted), record how long lifted.
                levLiftDur = millis() - levLiftTime;
              }
            }
            else { // not checking for lever lift
              prevLevState = 1;
              levLiftDur = 0;
            }
             
            // trigger REWARD if animal lifts paw during rewarded stim. (for long enough)
            if (levLiftDur >= liftLevThresh) { // count as response
                 //digitalWrite(optoPin, LOW); // REMOVE IF LASER SHOULD BE ON FOR WHOLE TRIAL
                 //digitalWrite(startPin, LOW); // turn off start pin at end of trial to trigger matlab
                 reward(); /////////////////// call reward function and print REWARD!!!!!
              }
            }  // end IF for levPressDur > 100 (REWARD sequence)        
       } // end WHILE elapTime <= stimDur (check for lever lifts)
           digitalWrite(optoPin, LOW);
           digitalWrite(startPin, LOW); // turn off start pin at end of trial to trigger matlab
        delay(25);   //added 180619 see if it helps with motor turning in wrong direction
           
      // MOVE STIM BACK
      digitalWrite(DIR_PIN,LOW); // Set Dir low = ccw
        for(x = 0; x < rotation; x++){ // Loop 200 times     
          digitalWrite(STEP_PIN,HIGH); // Output high
          delayMicroseconds(rotationSpeed); // Wait
          digitalWrite(STEP_PIN,LOW); // Output low
          delayMicroseconds(rotationSpeed); // Wait
        }
        
         prevLevState = 0;   // reset state variable to allow for consecutive triggers
         //prevType = 1; // for stimCount to promote alternation
         
     } // END of if stimType = 1 (rewarded trial)
     //////////////////////////////////catch trials
     
     else{
       Serial.println("catch trial");
       Serial.println(millis());
       //move stim away (no hall effect sensor used)
       digitalWrite(DIR_PIN,LOW);
       for(x = 0; x < rotation; x++){ // Loop 200 times  
        digitalWrite(STEP_PIN,HIGH); // Output high
        delayMicroseconds(rotationSpeed); // Wait
        digitalWrite(STEP_PIN,LOW); // Output low
        delayMicroseconds(rotationSpeed); // Wait
       }             
       // check if mouse lifts lever during catch trial
       elapTime = 0;
       prevLevState = 0;
       levPressDur = 0;
       startLevLiftCheck = 0;
       while (elapTime <= stimDuration) {
         currentTime = millis();
         elapTime = currentTime - trigTime; 
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
            // digitalWrite(optoPin, LOW);
            // digitalWrite(startPin, LOW); // turn off start pin at end of trial to trigger matlab
            punish();
           }
        }
       } // END while loop 
          digitalWrite(optoPin, LOW);
          digitalWrite(startPin, LOW); // turn off start pin at end of trial to trigger matlab
       //  move stimback to rest position
        delay(50);   //added 180619 see if it helps with motor turning in wrong direction
      digitalWrite(DIR_PIN,HIGH); //return to position
      for(x = 0; x < rotation; x++){ // Loop 200 times   
        digitalWrite(STEP_PIN,HIGH); // Output high
        delayMicroseconds(rotationSpeed); // Wait
        digitalWrite(STEP_PIN,LOW); // Output low
        delayMicroseconds(rotationSpeed); // Wait
      }
        prevLevState = 0;  //reset state variable for consecutive triggers
     }// END else 
   }
     delay(ITI); //inter-trial interval    

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
    elapTime = stimDuration + 100;  // break out of the reward stimulus loop after receiving reward
   
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
    elapTime = stimDuration + 100;  // 091311: need to check and make sure "elapTime1&2" are not in conflict
} // END of punish function

void cueTone() {  
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
// TONE WHEN MOTOR MOVES--HOPE TO MASK MOTOR SOUND
void startTone() {
   tone(speakerPin, 30000, 200); // frequency and duration
}   
