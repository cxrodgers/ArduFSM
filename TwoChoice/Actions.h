/* Various asynchronous actions.

These are protocol-specific, because for instance they assume certain
reward delivery configurations. They also rely on specific trial parameters
like reward durations. However they are often shared between related
protocols.

The main take_action function could be general, except for its dispatch
table from keywords to functions.

For now, let's keep these in an Actions.cpp for each protocol separately,
and then later, consider moving it to libraries/Actions.cpp or
libraries/TwoChoice_Actions.cpp.
*/

#ifndef __ACTIONS_H_INCLUDED
#define __ACTIONS_H_INCLUDED
int take_action(char *protocol_cmd, char *argument1, char *argument2);

void asynch_action_reward_l();
void asynch_action_reward_r();
void asynch_action_reward();
void asynch_action_set_thresh();
void asynch_action_light_on();
#endif