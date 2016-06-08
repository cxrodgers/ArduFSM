#MultiSens devlog
This is a reverse-chronological log of the development of this ArduFSM protocol, starting from after I had completed my own multisensory stimulation code from scratch but wanted to merge it into ArduFSM. I include it because I think it may be more accessible and expository than reading through reams of commit messages in the repo's git log. 

For help on using the most current version of MultiSens, see README.md.

##160505: How can we get object instantiations out of the main sketch? 

I've managed to accomplish this in MultiSens. There were two main things I had to do:

1) I defined a function in States.cpp that instantiates all of the state objects I need, puts pointers to them in an array, then returns the array (or more accurately, returns a pointer to the first element of the pointer array, which is equivalent to the array). I call this function from the main sketch to create an array of `TimedState` object pointers. This removes the need to explicitly instantiate each particular `TimedState` object at the beginning of `loop`.

Also, the main sketch makes some references to particular individual `TimedState` object constructors in `TRIAL_START` to reset the timers and update the durations for each object. I moved this functionality to `s_setup` for each `TimedState` object. `TimedState.s_setup()` executes automatically the first time `TimedState.run(time)` is called on a given trial. Moreover, `TimedState.run(time)` is called for all of the timed states that get executed on a given trial, so we're guaranteed that if a timed state gets executed, then its `run` function has been called, which means that its `s_setup` function has been called, which means that it has the most recent duration information from `param_values`. Thus, there's no need to call the constructor to do this from `TRIAL_START` in the main sketch.  

For convenience, in States.h, I use macros to define a number of indices into the states array so that I don't have to remember numeric indices for each state (in the same way that Chris used macros to define indices into `param_values`).

Then, in the main sketch, all references to particular `TimedState` objects are replaced with a reference to the states array along with the appropriate index. For example, 

    srw.run(time)

becomes

    states[stidx_RESPONSE_WINDOW]->run(time)     

However, calling functions from a `TimedState` pointer creates a problem with the `update` function, described below. 

2) `update` has to be changed to return nothing and take no arguments. As is, this is how `update` is defined in `TimedState`: `virtual void update`. However, `update` is then redefined with a new signature in States.cpp in several classes that inherit from `TimedState`. 

For example, in `TwoChoice`, we see `StateWaitForServoMove.update(Servo linServo)`, and `StateResponseWindow.update(uint16_int touched)`. 

Because these functions have different signatures from the one for `TimedState.update()`, they are not actually re-definitions of the `TimedState` virtual function. Rather, they are just regular functions of the inheriting class; they just happen to also be called update, but have no relation to `TimedState.update`.   

Moreover, it turns out that when we have our states array, its actual type is of pointer to the **parent** `TimedState` class. Even though the array includes pointers to objects that instantiate different inheriting classes `(StateWaitForServoMove, StateResponseWindow, etc.)`, each object ALSO instantiates the parent class TimedState, and THAT is the type that the pointers actually point to. 

Thus, when one tries to call 

    states[stidx]->update()

what you're actually calling is the TimedState function `update`, and NOT the `update` function of any of the inheriting classes. This means that `update` as used above must obey the syntax declared in `TimedState`, i.e., it takes nothing and returns void. If you try to pass it a `Servo` or `uint16_int`, you will get a compiler error saying that `TimedState` has no function called `update` that takes a `Servo` or a `uint16_int`.       

Given everything that `update` is intended to do currently, we can probably remove any arguments to it in the inheriting classes and keep it in conformity with the signature declared in TimedState.

For the time being, this is not much of a concern for me personally, because my partciular protocol does not make much use of the 'TimedState.update' function - I'm not attaching any servos or passing any 'touched' variables returned from the MPR121 library's 'pollTouchInputs' (I'm using Clay's analog lick detector on the 2P rig). However, this may be more of a concern for other existing protocols like TwoChoice.

For example, the `update` function of `StateResponseWindow` current takes the uint16_int variable touched as its input, then assigns the private variable `my_touched` to have the same value. In every case, however, the value of touched was just returned from a call to  `pollTouchInputs` earlier on in the main sketch. Could we just move the call to `pollTouchInputs` inside of `StateResponseWindow.update` and just have it return its value to `my_touched` directly?

The `update` function of `StateWaitForServoMove` takes a `Servo` object as its argument, then assigns it to a private variable `my_linServo` .  There's currently a comment in TwoChoice/States.cpp saying that this belongs in the constructor. We could try moving it there, but then we'd just have the same problem; the constructor can't take a `Servo` as an argument, because it needs to have the same signature as the `TimedState` constructor. But it seems that even the constructor shouldn't have to take a `Servo` object as an argument; we could declare linServo as extern in the global scope of States.cpp, then just assign `my_linServo = linServo` in the body of the constructor. 

One better would be to not just declare `linServo` as `extern` in the global scope of States.cpp, but to actually instantiate `linServo` in States.cpp and remove it from the main sketch. Currently, there are a few other references to `linServo` in the main sketch, but can these somehow be moved to States.cpp?    

In `INTER_TRIAL_INTERVAL`, we see `linServo.write(param_values[tpidx_SRV_FAR])`; it seems like we could wrap this line in a function that returns void and takes nothing, move the definition to States.cpp then just call that function from the main sketch. There are also a few lines that refer to `linServo` in `setup`, but it seems that these could also be moved to some `void servoSetup` function defined in States.cpp and just called from the main sketch. 

##160505: Created working MultiSens protocol in ArduFSM repo
A usable version of my multisensory stimulus protocol is now implemented in ArduFSM/MultiSens. I've run it in conjunction with testMultiSens160504, and verified that it works in the output file testMultiSens_output160504. 

###Remaining issues: 
In a departure from existing protocols, I've decided to make reward delivery coterminous with the stimulus. Now I need to decide how to deal with errors.

I suppose having a timeout makes sense because I don't want the animal licking indiscriminately to everything; I want to know that the mouse specifically associates reward with a particular stimulus condition, so I think a timeout may be necessary for shaping behavior.

But under what specific conditions should the timeout be introduced? Right now, the existing TwoChoice protocol only transitions into the timeout state if the animal makes a false alarm response during the response window, which follows the stimulus period. Since my rewards will be coterminous with the stimulus period, however, might I expect some licking during the stimulus period itself? And if so, should the timeout be triggered by licking during the stimulus period itelf? Does Chris punish licks during the stimulus period? (Also, why is the response Window so long?)

Here's what I think I should do:

On unrewarded trials, licks during the stimulus period should trigger a timeout AFTER the end of the stimulus period.

Should the timeout really be triggered after only ONE lick? Or should there be some higher threshold?

If the animal doesn't lick during the stimulus period, then there should STILL be a post-stimulus response window. If the animal licks during this time, go to the timeout state immediately.

How long should I make this response window? Does it really need to be 45 seconds? 

##160413:Planning my own MultiSensProtocol
So, if I want to pilot my own FSM, what states and parameters do I need?

States:
WAIT_FOR_TRIAL_START - doesn't require any functions
TRIAL_START - doesn't require any functions
STIM_PERIOD - class 
REWARD - non-class [can just never invoke for experiments without reward]
RESPONSE WINDOW - class [can just never invoke for experimejnts without reward]
ERROR - class [didn't think this was necessary, but may be necessary for shaping behavior so mouse isn't just licking to everything]
INTER-TRIAL INTERVAL - class 
POST_REWARD_PAUSE - class

param_vals:
stepper function index
speaker function index
overall stim duration
rewarded or not
reward duration

If I'm going to be giving reward, I might want to make reward coterminous with stimulus. in this case, does it make sense to make solenoid just another device like stepper and speaker? And like stepper and speaker, it can have an on time and an off time, and that on time can be a few hundred ms before the end of the overall stimulus period? 

Alternatively, doesn't the existing code already do something like start to deliver reward before the end of the stimulus period?

response_values:
whether or not it responded (can be binary for one pipe)
whether ot not this was a correct response (i.e, )

##160413: Some possible improvements
Given the understanding of ArduFSM described below, here are some ideas for possible improvements:

Currently, all of the TimedState objects are declared static at the beginning of loop(), and the timers are reset (using a syntax I don't understand) in the TRIAL_START switch case statement. This involves manually listing every TimedState object.

Would it be better if we could move references to individual TimedState objects to States.cpp? For example, rather than instantiating each one at the beginning of loop(), they could be instantiated in States.cpp, then we could have an function returning them in an array to the main sketch (like I do with devPtrs). Moreover, in the States source code, we could define indexes into the TimedState object array using macros, so that way all references to particular TimedState objects in the main sketch can be replaced with something like TimedStateArray[INDEX].

Also, in order to reset the timers on the TimedState objects, each object could have a resetTimer() function, and during the TRIAL_START switch case statement, the sketch could iterate through TimedStateArray and call each object's resetTimer() function.


##160413: Some outstanding questions
Here are some questions that remain for me after describing in the previous post how ArduFSM works and how it might be merged with my multisens_hw_control:

If I downlad ArduFSM as a subdirectory of an existing Arduino sketchbook (for exmaple, on a computer that already has other Arduino sketches), can this libraries folder stay in ArduFSM? Or do its contents have to be moved to the pre-existing sketchbok's library?*   

Do the non-class functions `state_rotate_stepper1`, etc., ever get used? It seems not

Why is `take_actions()` defined in the main sketch rather than in States.cpp?           

Also, how does this even work? The main sketch includes States.h, but States.h doesn't declare `param_values`; rather, `param_values` is defined in States.cpp. param_values is declared `extern` at the beginning of the main sketch, but isn't actually defined in any of the included code, so how does a function in the main sketch access `param_values`?

What data type exactly is `touched`?
 
What is this `sticky_touched` business?

Why is the `extern` declaration for `next_state` in States.cpp rather than States.h?

Why do these non-class functions take `next_state` by reference?

Once again, how does the extern reference actually work? The main sketch that instantiates the stepper object is not actually included in States.cpp. Can variables declared extern be defined in ANY linked file? And if so, what actually constitutes a linked file? I need to better understand the basic logic of how extern declarations work. 

How is the changing signature of `TimedState.update` allowed?    

Why is reward given in the move servo epoch??


##160413: Merging multisens_hw_control with ArduFSM
I would like to merge my personal code for multi-sensory stimulation with the ArduFSM framework that Chris developed. I've started this log to keep track of how the project has developed in a form that may be somewhat more accessible than going through reams of git commits.

The basic problem was that I had developed my own program from scratch, but I wanted to re-cast it in the ArduFSM framework in order to benefit from the features and flexibility already built into the latter, and as part of a broader effort to standardize code across the lab somewhat.

###Background on multisens_hw_control
multisens_hw_control is the program that I developed for presenting multiple Arduino-controlled sensory stimuli stimultaneosly. As of 160413, this program is saved on the "polymorphism" branch of my git repo multisens_hw_control, which I maintain at:

https://github.com/danieldkato/multisens_hw_control/tree/polymorphism

As described here, it appears to be working well enough in a few test cases that I'm satisfied with the feasibility of the general idea, and I'm now thinking about how to merge it into the existing ArduFSM framework.

The basic idea is that I need to be able to control multiple devices from an Arduino simultaneously (or nearly simultaneously) throughout the course of a stimulus presentation. I will also have to control some devices, like monitors, independently of the Arduino, but I can deal with that on the Python side of things - one thing that is clear is that I will AT LEAST have to control multiple devices near-simultaneously through an Arduino. 

####The naive approach:
For some stimuli, like brushing a pole through the whisker field, it is sufficient to issue some kind of "on" and "off" command (or "extend" and "retract," in this case) at the beginning and end of the stimulus period, respectively. 

####The problem with the naive approach: some devices may require constant updating
However, some stimuli may require constant updating throughout the stimulus period. One example of this is generating a white noise stimulus. While it would be convenient for me to somehow pre-load a white noise pattern at the beginning of the stimulus period then have the Arduino execute it over its duration, this is not the way Arduino's Tone library works. 

Rather, every time I want the tone generated by the speaker to change, the script must change the value of a tone variable associated with a Tone object, then call that Tone object's `play` command at the time that I want the actual sound coming out the speaker to change. Since I want the tone to be changing as close to constantly as possible, the sketch needs to be constantly making calls to Tone throughout the duration of the stimulus period. The same would be true if I wanted to generate any other acoustic stimulus as a function of time, like an exponential chirp, etc. 

####The naive approach redux: different while loops for each condition
Given these specific considerations, the most straightforward solution might be to just have steppers extend and retract at the beginning and end of each stimulus period, then have the tone constantly updating in a while loop that lasts for the duration of the stimulus period in between. 

Further, for each stimulus condition,  I could write a separate `while` loop. Then, during experiments, Python could supply the Arduino with a condition index on every trail, then have it decide which `while` loop to execute based on this index. In fact, this is what I currently do. 

####The problem with the naive approach redux: too many while loops
However, this solution will not generalize well. What if I want to add additional devices, like another stepper, or another solenoid? The number of different conditions I'd have to write would grow exponentially whenever I add devices to the Arduino. Supposing I have a stepper, a speaker, and a solenoid, and that I have only two states ("on" or "off") for each, I'd have to write 2^3  = 8 separate `while` loops. This is tractable enough, but if I wanted to add   another stepper, I'd have to write 2^4 = 16 different `while` loops. If I wanted to add another solenoid on top of that, I'd have to write 2^5 = 32 different `while` loops. Hard-coding these would be error prone, redundant, and would fundamentally fail to reflect the underlying logic that each device's state should be, in principle, independently manipulable.     

####A more flexible approach: object-oriented programming
One flexible way to solve this problem would be to make use of object-oritented programming, described here:

https://learn.adafruit.com/multi-tasking-the-arduino-part-1 

where different devices controlled by an Arduino are represented by objects that each have their own `update` function that is a function of time. On each pass of `loop`, each object's `update` function is called. 

For my purposes, `update` can be a function of some index that dictates what state one particular device should be in, and Python can supply such an index for each device on every trial. It can also be a function of time. So I like this object-oriented approach.

####An even more flexible approach: removing object instantiation from the main sketch
However, for my purposes, there is another shortcoming of the example linked to above. In it, `loop` refers to a fixed set of objects. This means that every time I want to change what devices are controlled by the Arduino, I would have to change the contents of `loop`. Since I may be making frequent changes to which devices are controlled by the Arduino (say between experiments running different conditions), this seems error-prone. 

It would be better if I could separate out the stuff that never has to change and save that in a main sketch that almost never gets tampered with, and then take those settings that are more likely to change on an experiment-by-experiment basis and then save those off in separate configuration files that can be specified at the beginning of each experiment. 

I've accomplished this by creating config.h and config.cpp, which are separate from the main sketch. They define a function called `config_hw`, which returns an array of device objects, each of which has their own `update` function. I can keep different config.h and config.cpp files for different experiment configurations, then somehow specify which one to use at the beginning of each experiment. 

The main sketch calls `config_hw` at the beginning of the file before `setup` or `loop` are called. This creates` devPtrs`, an array of pointers to device objects, in the global scope of the main sketch. Each pass of `loop` corresponds to a trial, and for the duration of the each trial, the sketch repeatedly iterates through devPtrs and calls each device's `update` function using `devPtrs->update`. As discussed above, `update` can be a function of some index that Python supplies for each device on the current trial, as well as of time.  

There are two constraints imposed by the above strategy that are worth noting. First, in order for all devices to be put in the same array, they must inherit from the same class. Thus, I have a parent `Device` class from which I derive specific classes for each device type like `Stepper`, `Speaker`, `Solenoid`, etc. 

Second, in order to use `->update` for each device in the array, `update` must be a virtual function of the parent class that is then defined for each child class. This means that for each child device class, `update` must have the same signature - i.e., it must take the same number and type of inputs, and must return the same type of output. In this context where `update` has different definitions in sibling classes, it is said to have the property of polymorphism. 

For the time being, `update` takes 4 arguments: a condition index, a start time, a stop time, and the time the trial started.This allows one to specify a device's behavior between an on time and an off time for any number of conditions. I'm not certain that this is the best signature, but it will serve my purposes for now. For testing purposes, each device class also has a `ping` function that just reports back its name. 

####The status quo:
So far, I have a test program that: 

1) defines, instantates and returns an array of device object pointers in a separate configuration file defining a `config_hw` function, 

2) creates an array of device object pointers devPtrs by calling `config_hw` from the main sketch 

3) on each trial, for the duration of a trial, iterates through devPtrs and calls each device's `ping` function. 

This test program works (at least at baud rates of 9600 and 115200), which leads me to conclude that an object-oriented, polymorphic approach can work.

###Background on ArduFSM
Now the question is how to take these strategies and implement them in the existing ArduFSM framework. The ArduFSM framework includes more functionality than I currently need, so it might be acceptable to just take a very pared-down version of ArduFSM and merge it with multisens_hw_control somehow. However, it's conceivable that I might ultimately want to start testing more sophisticated behaviors, in which case it may be more of a hassle to have to build out functionality by merging successive portions of ArduFSM piecewise; every round of this kind of expansion requires figuring out which pieces of ArduFSM can be merged independently of each other. Thus, it may be worthwhile to figure out how much ArduFSM functionality can be merged now without unacceptable amounts of superfluous functionality. 

I've written a detailed explanation of ArduFSM's functionality and how it works here:

https://github.com/danieldkato/ArduFSM/wiki/ArduFSM

###Merging multisens_hw_control and ArduFSM
`TimedState.loop` might be a reasonable place to iterate through `devPtrs`; that is, for the duration of the stimulus epoch, the switch case statement will call the `run` function of some `TimedState` object corresponding to the stimulus epoch. This in turn will call that `TimedState` object's `loop` function, each call of which will iterate once through the `devPtrs` array and call each device's `Device.update` function. `devPtrs` can be instantiated in the global scope of `States.cpp` so it can be accessed from any `TimedState`'s `loop` function.

Some issues to think about if I do it this way:

Will this require an `extern` declaration of `devPtrs` in the main sketch? It seems that putting `devPtrs` in the global scope of States.cpp would preclude the need for this, which would be preferable; that is, all references to `devPtrs` would be made from within States.cpp, so defining `devPtrs` within its global scope should be enough, and no declaration of `devPtrs` should be necessary in the main sketch. But param_values is also declared in the global scope of States.cpp and for some reason has an `extern` declaration in the main sketch. Why is this? It seems to be because there are multiple references to param_values in the main sketch itself, e.g. in `setup`, in `loop` when initializing timed state objects and in the switch case statement when echoing trial parameters back to the computer. If, by contrast, there will be no references to `devPtrs` in the main sketch itself, then maybe the `extern` declaration isn't necessary. (Also, relatedly, this makes me wonder if some of these functions that use param_values can be moved to States.cpp). 

My `Device.update` functions currently take a number of arguments, including a condition index, a start time, a stop time and the time of the trial start. How will `Device.update` get these arguments from inside `TimedState.loop`? I can't have `TimedState.loop` take those parameters as input arguments then pass them to `Device.update`, because `TimedState.loop` doesn't take any input arguments in its signature. I could change its signature, but because it's a polymorphic function, this would also change its signature in every other class that inherits from `TimedState`, which seems excessive.  

Perhaps the parameters could be (private) fields of the `TimedState` object that manages the stimulus epoch. This `TimedState` object could then also have its own function that takes some arguments from `param_values` then assigns their values to the private parameter fields, which are then referred to in `Device.update` when it is called from `TimedState.loop`.     







