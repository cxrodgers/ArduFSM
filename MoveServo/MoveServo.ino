/* Move servo close to nose for measuring
*/
#include "hwconstants.h"
#include <Servo.h>



/// not sure how to static these since they are needed by both loop and setup
// Servo
Servo linServo;

//// Setup function
void setup()
{
  Serial.begin(115200);
  unsigned long time = millis();  
  Serial.print(time);
  Serial.println(" DBG begin setup");

  //// Begin user protocol code
  //// Put this in a user_setup1() function?

  // attach servo
  linServo.attach(LINEAR_SERVO);
  linServo.write(1850); // move close for measuring

  delay(5000);
  linServo.write(1100); // move far for rotating
  
  delay(5000);  
  linServo.write(1850); // move close for measuring

}



//// Loop function
void loop()
{ /* Called over and over again. On each call, the behavior is determined
     by the current state.
  */
  
  //// Variable declarations
  // get the current time as early as possible in this function
  unsigned long time = millis();
  Serial.print(time);

  delay(1000);
  return;
}
