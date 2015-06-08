// Define the protocol specific parameters used in TwoChoice
//
// Boilerplate documentation for all protocols
// ---
// This should include macros for the indexes of every parameter and result 
// value, as well as the total number of parameters and results.
// The values and text abbreviation used to send over the serial port
// are defined in Params.cpp.
//
// No param can have a value of 0, because the conversion function returns
// 0 for unparseable data. So, 0 is the error value.
//
// To add a new param:
// 1) In Params.h, increment the value of N_TRIAL_PARAMS, and add a new
//    macro tpidx_PARAM_NAME with a value equal to N_TRIAL_PARAMS - 1.
// 2) In Params.cpp, add an abbreviated name to the end of param_abbrevs,
//    a default param value at the end of param_values, and a boolean to
//    the end of param_report_ET indicating whether the param should be
//    reported each trial.
// A similar procedure applies to adding a new result, except with
// N_TRIAL_RESULTS, results_abbrevs, results_values, and default_results_values.

#ifndef TWOCHOICE_PARAMS_H_
#define TWOCHOICE_PARAMS_H_

// Params
#define N_TRIAL_PARAMS 24
#define tpidx_STPPOS 0 // reqd
#define tpidx_MRT 1 // latch
#define tpidx_REWSIDE 2 // reqd
#define tpidx_SRVPOS 3 //reqd
#define tpidx_ITI 4 // init-usually
#define tpidx_2PSTP 5 // init-only
#define tpidx_SRV_FAR 6 // init-usually
#define tpidx_SRV_TRAVEL_TIME 7 // init-usually
#define tpidx_RESP_WIN_DUR 8 // init-usually
#define tpidx_INTER_REWARD_INTERVAL 9 // init-usually
#define tpidx_REWARD_DUR_L 10 // init-usually
#define tpidx_REWARD_DUR_R 11 // init-usually
#define tpidx_SERVO_SETUP_T 12 // init-only
#define tpidx_PRE_SERVO_WAIT 13 // init-usually
#define tpidx_TERMINATE_ON_ERR 14 // latched
#define tpidx_ERROR_TIMEOUT 15 // latched
#define tpidx_STEP_SPEED 16 // init-only
#define tpidx_STEP_FIRST_ROTATION 17 // init-usually
#define tpidx_STEP_INITIAL_POS 18 // init-only
#define tpidx_IS_RANDOM 19 // reqd
#define tpidx_TOU_THRESH 20 // init-only
#define tpidx_REL_THRESH 21 // init-only
#define tpidx_STP_HALL 22
#define tpidx_STP_POSITIVE_STPPOS 23 

// Results
#define N_TRIAL_RESULTS 2
#define tridx_RESPONSE 0
#define tridx_OUTCOME 1


//// Provide hooks to these parameters and results so that files that include
// this will be able to access them.
extern char* param_abbrevs[N_TRIAL_PARAMS];
extern long param_values[N_TRIAL_PARAMS];
extern bool param_report_ET[N_TRIAL_PARAMS];
extern char* results_abbrevs[N_TRIAL_RESULTS];
extern long results_values[N_TRIAL_RESULTS];
extern long default_results_values[N_TRIAL_RESULTS];


//// Boiler plate getter functions. These are used by ArduFSM library because
// it can't use the hooks above.
long* get_param_values();
long* get_results_values();
char** get_results_abbrevs();
char** get_param_abbrevs();
int get_n_trial_params();
int get_n_trial_results();
bool* get_param_report_ET();
long* get_default_results_values();

#endif // TWOCHOICE_PARAMS_H_