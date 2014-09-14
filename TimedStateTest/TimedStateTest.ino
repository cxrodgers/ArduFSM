
class TimedState
{
  protected:
    unsigned long timer = 0;
    unsigned long duration = 0;
    virtual void s_setup();
    virtual void loop();
    virtual void s_finish();
  
  public:
    TimedState(unsigned long t, unsigned long d) : timer(t), duration(d) { };
    void run(unsigned long time);
};

void TimedState::run(unsigned long time)
{
  // boiler plate timer code
  if (timer == 0)
  {
    s_setup();
    timer = time + duration;
  }
  
  if (time < timer)
  {
    loop();
  }
  else
  {
    s_finish();
    timer = 0;
  }
};


/* User completes this part */
class State1 : public TimedState {
  protected:
    int var = 0;  
  void s_setup();  
  void loop();
  void s_finish();
  
  public:
    State1(unsigned long t, unsigned long d) : TimedState(t, d) { };
};

void State1::s_setup()
{
  Serial.println((String) "State1 setup " + ' ' + timer); 
}

void State1::loop()
{
  Serial.println((String) "State1 loop " + ' ' + timer); 
}

void State1::s_finish()
{
  Serial.println((String) "State1 finish " + ' ' + timer); 
}
/* End user part */


unsigned long d1 = 5000;
State1 ts1(0, d1);


void setup()
{
  Serial.begin(9600);
  Serial.println("setup");
}

void loop()
{
  ts1.run(millis());
  delay(1000);
}
