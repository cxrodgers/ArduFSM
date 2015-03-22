// Define the protocol specific parameters used in SimpleTrialRelease
//
// Boilerplate documentation for all protocols
// ---
// This should include macros for the indexes of every parameter and result 
// value, as well as the total number of parameters and results.
// The values and text abbreviation used to send over the serial port
// are defined in Params.cpp.

#ifndef SIMPLETRIALRELEASE_PARAMS_H_
#define SIMPLETRIALRELEASE_PARAMS_H_

// Params
#define N_TRIAL_PARAMS 1
#define tpidx_ITI 0

// Results
#define N_TRIAL_RESULTS 1
#define tridx_RESPONSE 0

// Provide hooks to these parameters and results so that files that include
// this will be able to access them.
extern char* param_abbrevs[N_TRIAL_PARAMS];
extern long param_values[N_TRIAL_PARAMS];
extern bool param_report_ET[N_TRIAL_PARAMS];
extern char* results_abbrevs[N_TRIAL_RESULTS];
extern long results_values[N_TRIAL_RESULTS];
extern long default_results_values[N_TRIAL_RESULTS];

#endif // SIMPLETRIALRELEASE_PARAMS_H_