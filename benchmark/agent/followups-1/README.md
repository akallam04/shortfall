# Plan followups-1

[The plan](../plans/followups-1.yaml) ran two follow-up experiments on the unguided task with feedback none, each compared with the no-feedback arm of `claude-haiku-5-5` on prompt version v2. Its tests were written into the plan file and pushed before the first trial.

- **budget2-none**: `claude-haiku-5-5` on prompt version v2-budget2, where the agent cannot end a trial while more than 60 runs are left. 10 trials.
- **sonnet-none**: `claude-sonnet-5-5` on prompt version v2. 10 trials.
- **budget-none**: `claude-haiku-5-5` on prompt version v2-budget, closed after 3 trials, described below.

The results, the tests and what they mean are in [RESULTS.md](../../../RESULTS.md#6-follow-up-experiments-the-whole-budget-and-a-bigger-model), and every trial is listed on [the agent trials page](../README.md#plan-followups-1). Each trial folder has the layout described [there](../README.md#what-each-trial-folder-holds). The prompt hashes are [prompts.sha256](prompts.sha256) for v2, [prompts-v2-budget.sha256](prompts-v2-budget.sha256) and [prompts-v2-budget2.sha256](prompts-v2-budget2.sha256).

## Held trials

Three trials were held after the plan, because one cart became two orders in a run with two servers and the default in-memory lock: sonnet-none-3, sonnet-none-5 and budget2-none-6, which had it in 3 of its attempts. Each held test was reviewed by hand, as the plan file sets out, with 100 runs as is, 100 with Redis locking, 100 with all completions sent to server 1, and 100 with pr-17420 for information only. No check failed with Redis locking or on server 1, so each trial is labeled "documented limit of in-memory locking" and published with its review runs in its `review/` folder. The counts are in [RESULTS.md](../../../RESULTS.md#held-trials-reviewed-by-hand).

## Trials run again from scratch

- **sonnet-none-3** was stopped by the safety rule after one cart became two orders, before that failure was in the list of covered failures. The stopped record is in [../stopped/followups-1-sonnet-none-3](../stopped/followups-1-sonnet-none-3/), and the rerun is [sonnet-none-3](sonnet-none-3/).
- **sonnet-none-4** was interrupted twice by problems on our side, never by the model. First, the terminal session that started the plan closed and took the engine with it. Then, after the engine restarted, Oversold's database was not running and the next try stopped with an error about image inputs. Both records stay unpublished and are not counted, and [sonnet-none-4](sonnet-none-4/) is the run from scratch after them. In that run the model put its scenario inside the text of its hypothesis in all 7 submissions, so each was refused for having no scenario, and it then called finish without running a test. It counts as a miss.

## budget-none: closed after 3 trials, design flaw

Arm budget-none ran `claude-haiku-5-5` on prompt version v2-budget. While more than 60 runs were left, the agent could not end the trial: when it called finish, or replied without a tool call, the loop answered with one fixed line, and each of those answers used up one of the 100 turns. In 2 of the 3 trials the agent kept replying without a tool call, waiting for run results that this mode never shows, and reached the 100-turn cap after 119 and 129 runs. So the arm could not tell whether stopping early is what held the agent back.

The arm was closed after 3 trials and replaced by budget2-none on prompt version v2-budget2, where the line says that run results never come in this mode, gate answers do not count toward the turn cap, and a trial ends after 15 gate answers. The 3 budget-none trials are kept here as they ran, in [budget-none-1](budget-none-1/), [budget-none-2](budget-none-2/) and [budget-none-3](budget-none-3/).
