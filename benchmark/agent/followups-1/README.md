# Plan followups-1

[The plan](../plans/followups-1.yaml) runs two follow-up experiments on the unguided task with feedback none, each compared with the no-feedback arm of `claude-haiku-5-5` on prompt version v2. Its tests were written into the plan file and pushed before the first trial. The results are added here when the plan is done.

## budget-none: closed after 3 trials, design flaw

Arm budget-none ran `claude-haiku-5-5` on prompt version v2-budget. While more than 60 runs were left, the agent could not end the trial: when it called finish, or replied without a tool call, the loop answered with one fixed line, and each of those answers used up one of the 100 turns. In 2 of the 3 trials the agent kept replying without a tool call, waiting for run results that this mode never shows, and reached the 100-turn cap after 119 and 129 runs. So the arm could not tell whether stopping early is what held the agent back.

The arm was closed after 3 trials and replaced by budget2-none on prompt version v2-budget2, where the line says that run results never come in this mode, gate answers do not count toward the turn cap, and a trial ends after 15 gate answers. The 3 budget-none trials are kept here as they ran, in [budget-none-1](budget-none-1/), [budget-none-2](budget-none-2/) and [budget-none-3](budget-none-3/).
