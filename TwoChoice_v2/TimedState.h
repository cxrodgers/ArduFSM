#ifndef __TIMEDSTATE_H_INCLUDED__
#define __TIMEDSTATE_H_INCLUDED__

#include "Arduino.h"
/*

Template for a waiting state. Try to make it match this syntax.
case A_WAITING_STATE:
  // Wait the specified amount of time
  if (state_timer == -1)
  {
    // Start timer and run first-time code
    state_timer = time + WAITING_TIME;

    a_waiting_state_run_once();
  }
  else
  {
    a_waiting_state_run_many_times();
  }
  
  if (time > state_timer)
  {
    a_waiting_state_run_when_done();
    
    // Check timer and run every-time code
    next_state = NEXT_STATE;
    state_timer = -1;
  }
  break;

Eventually this could be some kind of object:
case A_WAITING_STATE:
  waiting_state_obj.run();

Where the object derives from something that implements the basic pattern
above, and the user just filles in the run_once(), run_many_times(), etc
*/

class TimedState
{
  protected:
    unsigned long timer = 0;
    unsigned long duration = 0;
    bool flag_stop = 0;
    virtual void s_setup() {};
    virtual void loop() {};
    virtual void s_finish() {};
  
  public:
    TimedState(unsigned long d) : duration(d) { };
    void run(unsigned long time);
    virtual void update() {};
};

#endif
