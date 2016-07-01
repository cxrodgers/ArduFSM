#Quick setup guide to creating a new protocol 


##1: Create the protocol directory.
Create a new folder in ArduFSM and name it for the protocol you are creating. It will need at least a main sketch, a States.h file and a States.cpp file. It may be useful to begin by copying over and renaming another protocol folder.


##2: Identify the states of the task. 
A flow chart could be helpful in visualizing this. For every epoch of the task, define all of the possible subsequent epochs (e.g., following a response window epoch, the task could either go to a reward epoch for correct responses, a timeout period for false alarms, or an intertrial interval for nogo responses). Things should eventually loop around in order to accommodate multiple trials. The states should map roughly onto the nodes of a flow chart. These states should be listed in the protocol's States.h between the curly brackets in the line : 

    enum STATE_TYPE{}  

Note that you should NOT list these states as Strings; just type the name of the state without any quotes (what this statement is actually doing is creating a new *type* of variable, `STATE_TYPE`, and listing all of its possible values). 


##3: Identify the trial parameters of the task. 
Count them up and set the number of trial parameters for the protocol in States.h using: 

    #define N_TRIAL_PARAMS <number>

where '<number>' stands in for the number of trial parameters. This will make the array `param_values` the appropriate length. Now, each element in this array can represent one trial parameter. 

Choose an ordering for the trial parameters so that each element of `param_values` always represents the same trial parameter. Remembering an arbitrary numeric index for each trial parameter may be inconvenient if there are many trial parameters, so it may be worthwhile to substitute numeric indices with sensible names that more obviously refer to some trial parameter. To do so, in States.h, use the syntax: 

    #define <idxName> <idxValue> 

for each trial parameter, where `<idxValue>` stands in for the numeric index of that trial parameter in `param_values`, and `<idxValue>` stands in for some more readily human-interpretable name that will be treated as equivalent to `<idxValue>`. Then on, `param_values[<idxName>]` will be equivalent to `param_values[<idxValue>]`.  


##4: Decide on abbreviations for each trial parameter. 
These can be used by the computer to communicate parameter values to the Arduino, and used by the Arduino to recognize which parameters the computer is talking about. List these as Strings (i.e., enclosed by double quotes) in States.cpp in: 

    char* param_abbrevs[N_TRIAL_PARAMS] = {} 


##5: Choose default values for each trial parameter. 
Using the ordering you chose in step #3, list the default value for each parameter in States.cpp using:

    long param_values[N_TRIAL_PARAMS] = {}  


##6: Decide which trial parameters you want reported back to the computer on each trial. 
Using 1 for yes and 0 for no, set these in  in: 

    bool param_report_ET[N_TRIAL_PARAMS] = {}  


##7: Identify the results parameters. 
Count them up and enter the number of results parameters in State.h using: 

    #define N_TRIAL_RESULTS <number> 

where `<number>` stands in for the number of results parameters. This will make the array `results_values` the appropriate length. Choose an ordering for these as you did for trial parameters in step #3.   


##8: Decide abbreviations for each result parameter. 
List these as Strings (i.e., enclosed by double quotes) in States.cpp using: 

    char* results_abbrevs[N_TRIAL_RESULTS] = {}.


##9: Decide default values for each results parameter. 
List these in States.cpp in: 

    long results_values[N_TRIAL_RESULTS] = {}. 


##10: Write the functions corresponding to each state.
For each state, decide whether the amount of time it must last could be a reasonable amount of time for one pass of `loop()` (on the order of milliseconds, e.g. opening a reward valve or rotating a stepper), or if it is the kind of state that needs to persist over several passes of `loop()` (e.g. some task epoch that must last on the order of seconds). 

If the former, declare a non-class function for it in States.h and define it in States.cpp. So far, these have all returned an int (which encodes some status message) and taken a reference to next_state as an input argument. 

If the latter, declare a class for it in States.h that inherits from `TimedState`. Declare whatever variables or functions it needs in addition to what it inherits from `TimedState`. After declaring the class, redefine its `s_setup()`, `loop()`, `s_finish()` and `update()` functions in States.cpp if necessary (these do nothing by default).     

If your states need to refer to any devices that are represented by objects from the standard Arduino libraries - like `Stepper` or `Servo` - the practice thus far has been to instantiate these in the main sketch, then declare them as extern in States.cpp. This will allow your state functions to refer to them in States.cpp even though they're actually instantiated elsewhere. 

These functions are also where you build in the logical structure of the experiment; at the end of each non-class function, and at the end of `s_finish()` for each class, specify what the `next_state` should be (or write an if statement that determines what the next state should be given some condition).


##11: Instantiate any states represented by objects.
For each state that is represented by a class, instantiate it at the beginning of `loop()` in the main sketch using the syntax: 

    static <StateClass> <state_instance>(<params>)

where `<StateClass>` stands in for the corresponding class, `<state_instance>` stands in for the name of an instance of that class you are creating, and `<params>` stands in for the parameters you are initializing the instance with. The `static` means that the object will only be instantiated on the first pass of `loop()`, so that it's not re-created over and over again on every pass.    


##12: Add your states to the `switch case` statement.


##13: From each state, call the corresponding state functions. Optionally, print any information you want back to the computer.  


##14: Instantiate any hardware objects in the main sketch. 
As discussed in step #10, the practice thus far has been to instantiate any standard Arduino objects in the main sketch. The reason for this is that the main sketch needs to refer to these objects in `setup()`. 

[Although could not just declare these extern and define them in States.cpp? I suppose it wouldn't actually save us any work in the main sketch if we still have to remember to declare them extern there]
