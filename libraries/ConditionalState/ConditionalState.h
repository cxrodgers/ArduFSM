#ifndef __CONDTIONALSTATE_H_INCLUDED__
#define __CONDTIONALSTATE_H_INCLUDED_

#include "Arduino.h"

class ConditionalState
{
  protected:
    virtual bool end_condition() {};
    virtual void s_loop() {};
    virtual void s_finish() {};
  
  public:
    ConditionalState() {};
    void run();

};

#endif
