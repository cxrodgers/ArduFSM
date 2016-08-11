#ifndef __STATES_H_INCLUDED__
#define __STATES_H_INCLUDED__

#include "hwconstants.h"
#include "TimedState.h"


#define N_TRIAL_PARAMS 2
#define tpidx_LIGHTON_DUR 0
#define tpidx_LIGHTOFF_DUR 1

//States
enum STATE_TYPE
{
  LIGHT_ON,
  LIGHT_OFF,

};

void stateDependentOperations(STATE_TYPE current_state, unsigned long time);


//Declare States
class StateLightOn : public TimedState {
  protected:
    void s_setup();
    void s_finish();    

  public: 
    StateLightOn(unsigned long d) : TimedState(d) { };
};

class StateLightOff : public TimedState {
  protected:
    void s_setup();
    void s_finish();    

  public: 
    StateLightOff(unsigned long d) : TimedState(d) { };
};







#endif
