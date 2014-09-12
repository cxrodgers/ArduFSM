// Define all constants that are true for all rigs
// Rig-specific changes can be made by setting parameters in the usual way
// Otherwise we need different versions of the protocol


//// DIGITAL

// Two-pin mode
#define TWOPIN_ENABLE_STEPPER 11
#define TWOPIN_STEPPER_1 12
#define TWOPIN_STEPPER_2 13

// Four-pin mode
#define ENABLE_STEPPER 12
#define PIN_STEPPER1 8
#define PIN_STEPPER2 9
#define PIN_STEPPER3 10
#define PIN_STEPPER4 11

// Rewards
#define L_REWARD_VALVE 6
#define R_REWARD_VALVE 7
#define TOUCH_IRQ 2



//// ANALOG

// Servo
#define LINEAR_SERVO 4
