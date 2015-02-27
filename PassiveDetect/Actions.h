/* Header file for TwoChoice-related actions */

#ifndef __ACTIONS_H_INCLUDED
#define __ACTIONS_H_INCLUDED
int take_action(char *protocol_cmd, char *argument1, char *argument2);
void asynch_action_reward_l();
void asynch_action_reward_r();
void asynch_action_set_thresh();
void asynch_action_light_on();
#endif