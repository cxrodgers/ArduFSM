// Params used by SimpleTrialRelease

#include "Params.h"

char* param_abbrevs[N_TRIAL_PARAMS] = {
  "ITI"
  };
  
long param_values[N_TRIAL_PARAMS] = {
  2000
  };

// Whether to report on each trial  
// Currently, manually match this up with Python-side
// Later, maybe make this settable by Python, and default to all True
// Similarly, find out which are required on each trial, and error if they're
// not set. Currently all that are required_ET are also reported_ET.
bool param_report_ET[N_TRIAL_PARAMS] = {
  1
};
  

//// Results
char* results_abbrevs[N_TRIAL_RESULTS] = {};
long results_values[N_TRIAL_RESULTS] = {};
long default_results_values[N_TRIAL_RESULTS] = {};