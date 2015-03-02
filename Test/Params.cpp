#include "Params.h"


char* param_abbrevs[N_TRIAL_PARAMS] = {
  "NSTPS", "MRT", "ITI", "2PSTP", "RWIN", 
  "IRI", "RD_L", "RD_R", "STPSPD", "TOUT", 
  "RELT", "STPT", "ISGO",
  };
  
long param_values[N_TRIAL_PARAMS] = {
  3, 1, 3000, 3, 2000,
  500, 50, 50, 20, 6,
  6, 10, 3
  };

// Whether to report on each trial  
// Currently, manually match this up with Python-side
// Later, maybe make this settable by Python, and default to all True
// Similarly, find out which are required on each trial, and error if they're
// not set. Currently all that are required_ET are also reported_ET.
bool param_report_ET[N_TRIAL_PARAMS] = {
  1, 0, 1, 0, 0,
  0, 0, 0, 0, 0,
  0, 0, 1
};
  
char* results_abbrevs[N_TRIAL_RESULTS] = {"RESP", "OUTC"};
long results_values[N_TRIAL_RESULTS] = {0, 0};
long default_results_values[N_TRIAL_RESULTS] = {0, 0};