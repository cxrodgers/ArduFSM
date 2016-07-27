#include "ConditionalState.h"

void ConditionalState::run() {
  if ( end_condition() ) {
    s_finish();
  }
  else {
    s_loop();
  }

};
