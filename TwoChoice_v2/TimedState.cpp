#include "TimedState.h"

void TimedState::run(unsigned long time)
{ /* Boilerplate 'run' code for a state with a certain length of time.
    
  This is called on every pass, as long as the FSM is in this state.
  Depending on the current state of the timer, flag_stop, and the time, this
  calls s_setup(), loop(), or s_finish().

  States that inherit from this should define their own s_setup(), loop(),
  and s_finish().
    
  Simple algorithm:
    * If the timer is set to 0, take this to mean that we haven't started yet.
      Run s_setup()
      Set the timer and the flag
    * If the time is greater than the timer, or the flag_stop has been set,
      run the s_finish()
    * Otherwise, run loop()
  */
  // always store time of last call
  time_of_last_call = time;    
    
  // boiler plate timer code
  if (timer == 0)
  {
    s_setup();
    flag_stop = 0;
    timer = time + duration;
  }
  
  if (flag_stop || (time >= timer))
  {
    s_finish();
    timer = 0;      
  }
  else
  {
    loop();
  }
};

