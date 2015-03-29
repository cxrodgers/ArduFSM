// Params used by TwoChoice

#include "Params.h"

char* param_abbrevs[N_TRIAL_PARAMS] = {
  "STPPOS", "MRT", "RWSD", "SRVPOS", "ITI",
  "2PSTP", "SRVFAR", "SRVTT", "RWIN", "IRI",
  "RD_L", "RD_R", "SRVST", "PSW", "TOE",
  "TO", "STPSPD", "STPFR", "STPIP", "ISRND",
  "TOUT", "RELT", "STPHAL", "HALPOS",
  };

long param_values[N_TRIAL_PARAMS] = {
  1, 1, 1, 1, 3000,
  0, 1900, 100, 1000, 500,
  40, 40, 1000, 1, 1,
  6000, 20, 50, 50, 0,
  6, 3, 0, 50
  };

// Whether to report on each trial  
// Currently, manually match this up with Python-side
// Later, maybe make this settable by Python, and default to all True
// Similarly, find out which are required on each trial, and error if they're
// not set. Currently all that are required_ET are also reported_ET.
bool param_report_ET[N_TRIAL_PARAMS] = {
  1, 0, 1, 1, 0,
  0, 0, 0, 0, 0,
  0, 0, 0, 0, 0,
  0, 0, 0, 0, 1,
  0, 0, 0, 0
};

//// Results
char* results_abbrevs[N_TRIAL_RESULTS] = {"RESP", "OUTC"};
long results_values[N_TRIAL_RESULTS] = {0, 0};
long default_results_values[N_TRIAL_RESULTS] = {0, 0};



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