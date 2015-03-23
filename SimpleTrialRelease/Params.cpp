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
char* results_abbrevs[N_TRIAL_RESULTS] = {
  "RESP"
  };
long results_values[N_TRIAL_RESULTS] = {
  0
  };
long default_results_values[N_TRIAL_RESULTS] = {
  0
  };


//// Boilerplate getter functions
// These are needed by ArduFSM library
// Can we move them into a separate file since this will not change?  
long* get_param_values() {
  return param_values;
}

long* get_results_values() {
  return results_values;
}

char** get_results_abbrevs() {
  return results_abbrevs;
}

char** get_param_abbrevs() {
  return param_abbrevs;
}

int get_n_trial_params() {
  return N_TRIAL_PARAMS;
}

int get_n_trial_results() {
  return N_TRIAL_RESULTS;
}

bool* get_param_report_ET() {
  return param_report_ET;
}

long* get_default_results_values() {
  return default_results_values;
}