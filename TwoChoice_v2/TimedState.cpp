#include "TimedState.h"

void TimedState::run(unsigned long time)
{
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

