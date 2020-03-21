// digital input from master arduino
const int input_pin = 2;

// output to the laser
const int output_pin = 3;

// how long the shutter is open (us)
const unsigned int pulse_duration_us = 3000;

// how long to wait between pulses (ms)
const unsigned long inter_pulse_interval_ms = 123;
const unsigned int inter_pulse_interval_us = 500;

// how long to wait after trigger before first pulse
const unsigned long post_trigger_wait_ms = 700;

void setup() {
  pinMode(output_pin, OUTPUT);      
  pinMode(input_pin, INPUT);     
}

void loop() {
  // only pulse if input is high
  if (digitalRead(input_pin) == HIGH) {
    // wait after trigger
    // this provides noise rejection
    // and also a delay between trial start and laser
    delay(post_trigger_wait_ms);
    
    // Repeatedly pulse until it goes low again
    while (digitalRead(input_pin) == HIGH) {
      // Pulse
      digitalWrite(output_pin, HIGH);
      delayMicroseconds(pulse_duration_us);
      digitalWrite(output_pin, LOW);
      
      // Wait
      delay(inter_pulse_interval_ms);      
      delayMicroseconds(inter_pulse_interval_us);
    }
  }
}
 
