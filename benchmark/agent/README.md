# Agent trials

This page explains, in plain words, what the AI agent has done so far, and lists every trial it has run.

## What a trial is

A trial gives the agent one task and a fixed budget of runs, attempts, turns and dollars. Every trial so far had at most 300 runs and $1. Trials on prompt version v1 also had at most 12 attempts and 60 turns, and trials on v2 at most 30 attempts and 100 turns. A turn is one reply from the AI model. A run is one go of a test on a fresh private copy of the shop.

During a trial the agent reads Medusa's source code and then submits attempts. Each attempt is a small test scenario plus a guess: the source file it thinks holds the problem, one cause from a fixed list (not on prompt version v2-nomenu, described below), and the one check it expects to fail. The guess is saved before the test runs, so it cannot be changed once the result is known. When the agent is done, it calls finish and lists its claims.

## Guided and unguided

In a guided trial the agent gets the public bug report for one known bug, like an open-book test. The report describes what goes wrong and often names the source file involved. So a guided trial shows whether the agent can turn a bug report into a test that reproduces the bug. It does not show whether the agent can find a bug on its own.

In an unguided trial the agent gets no bug report. It has to decide on its own where a rule might break. This is the fair comparison with the two simple methods that use no AI, which have the same 300-run budget.

There are two feedback modes:

- **none**: after each attempt the agent only learns whether the attempt was accepted, and how many attempts and turns it has left (on v1 also how many runs).
- **history**: it also sees, for the runs on plain Medusa, how often each check failed and a short summary of each run.

## The three results

Every attempt that runs gets three results:

- **Violation**: a check failed in at least one run on plain Medusa 2.22.0.
- **Reproduced**: the failure matches one of the benchmark's three test scenarios, and the same test passes on a copy of Medusa with the public fix for that bug.
- **Named the right place**: the file and the cause the agent gave with the attempt, before its runs, both match the answer key for that test scenario. The ledger and `score.json` call this result `located`.

## Claims

At the end, the agent lists claims: the attempts it believes found a real problem, each with a file and a cause. A claim is **backed by a violation** when that attempt had a violation on plain Medusa. It is **not backed by a violation** when that attempt had no violation, was refused or never ran.

In the none mode the agent never sees any results, so a claim not backed by a violation there is a false alarm. In the history mode it sees the results, so its claims should be backed by a violation.

The file and the cause in a claim are recorded as the agent's diagnosis after results. They are graded on their own, in `claims.json`, and never replace the file and the cause saved with the attempt before its runs. Those saved values are the only prediction, and named the right place uses only them.

## Prompt versions

Everything the agent is shown, and the settings of its loop, are fixed by one hash before any trial of a plan runs. Each plan folder holds the hash it used.

- **v1** ([hash](guided-haiku-1/prompts.sha256)) was used by guided-haiku-1.
- **v2** ([hash](prompts.sha256)) is used by unguided-haiku-1, guided-haiku-2, the v2 arms of scale-10 and the sonnet-none arm of followups-1, which runs it with `claude-sonnet-5-5`.
- **v2-nomenu** ([hash](prompts-v2-nomenu.sha256)) is v2 without the list of causes. The agent names only a file for each attempt and each claim. It was used only by the v2-nomenu arm of scale-10, to test whether the list of causes helps.
- **v2-budget** ([hash](prompts-v2-budget.sha256)) is v2 with one change to the loop: while more than 60 runs are left, the agent cannot end the trial. If it calls finish, or replies without a tool call, it gets one fixed line: "Finish is not available yet. Keep testing until the run budget is nearly used." It was used by plan [followups-1](plans/followups-1.yaml) for 3 trials, and then closed: each gate answer used up a turn, and the agent often kept replying without a tool call while it waited for run results that this mode never shows.
- **v2-budget2** ([hash](prompts-v2-budget2.sha256)) replaces v2-budget. The gate line is "Finish is not available yet. In this mode you never see run results, so don't wait for them. Submit another attempt until the run budget is nearly used." Gate answers do not count toward the 100-turn cap, and the trial ends after 15 gate answers. Until the gate first answers, its requests are the same as v2-budget's. It is used by plan [followups-1](plans/followups-1.yaml).

v2 was written after the guided v1 results were known. The unguided trials ran only on v2 and v2-nomenu. What changed from v1 to v2, and why:

- In the none feedback mode the agent no longer sees how many runs are left, only attempts and turns. On v1 the run count told it, indirectly, whether an attempt had found something, because an attempt that finds something gets extra runs to confirm it.
- The budget is now 300 runs, 30 attempts and 100 turns, so the run budget is the real limit, as it is for the two simple methods. The agent is told that the budget is for finding as many distinct problems as it can, and that one finding does not end the task.
- In guided trials the agent is told to check that its scenario matches the conditions the bug report describes before it claims the reported bug. On v1, given the #17032 report, the agent tested on one server, while that report describes two.
- Medusa's Enterprise Edition files are hidden from the agent's tools, because they are not under the MIT license.
- Old tool results are now shortened in batches every 6 turns instead of one per turn. This lets more of each request be read from the prompt cache, which costs less.

## Headline: 10 unguided trials per method

Each cell says in how many of 10 trials the test scenario was reproduced, and the median runs to its first reproduction over all 10 trials. A trial that missed the scenario counts as over 300 runs, so when half or more of the 10 trials missed it, the median is over 300. Every method had a budget of 300 runs per trial. The two simple methods are described in [../README.md](../README.md#baselines). Trials 1 to 3 of each column are the earlier ones, in [../baselines/2004ed5/](../baselines/2004ed5/) and [unguided-haiku-1/](unguided-haiku-1/). Trials 4 to 10 come from [plan scale-10](#plan-scale-10).

| Test scenario | Grid (no AI) | Random (no AI) | Agent, feedback none | Agent, feedback history |
|---|---|---|---|---|
| medusa-17032-last-unit | 10 of 10, median 58.5 | 9 of 10, median 110 | 7 of 10, median 33 | 5 of 10, median over 300 |
| medusa-17032-counter | 10 of 10, median 33 | 10 of 10, median 46.5 | 7 of 10, median 33 | 6 of 10, median 48 |
| medusa-16502-lines | 10 of 10, median 54 | 7 of 10, median 135.5 | 3 of 10, median over 300 | 2 of 10, median over 300 |
| All three in one trial | 10 of 10 | 6 of 10 | 3 of 10 | 0 of 10 |

What the table shows:

- The grid reproduced all three test scenarios in every one of its 10 trials. The agent did that in at most 3 of 10.
- On medusa-17032-counter the grid tied the agent with feedback none: a median of 33 runs each. The grid reproduced it in 10 of 10 trials, the agent in 7 of 10.
- On medusa-17032-last-unit the agent with feedback none had the lower median, 33 runs against the grid's 58.5, but it reproduced the scenario in 7 of 10 trials against the grid's 10 of 10. Once its misses count, this speed gap could be chance.
- The agent tested two cart lines that use the same stock in only 3 of 10 trials with feedback none and 4 of 10 with feedback history, so it reproduced medusa-16502-lines in 3 and 2 of 10.
- When the first attempt fails at once, a #17032 scenario is usually counted at run 33: 3 screen runs, 10 scoring runs and two controls of 10 runs. Many cells sit at 33 for that reason.
- The grid was designed with knowledge of the bug shapes in the scenarios, so it is an informed baseline, not a blind one.

Named the right place, for the agent: with feedback none, the file and the cause matched the answer key in 6 of the 7 trials that reproduced each #17032 scenario, and in the 7th only the cause matched. For medusa-16502-lines the cause matched and the file did not, in all 3. With feedback history, both matched in 4 of 5 reproductions of medusa-17032-last-unit and 5 of 6 of medusa-17032-counter, and only the cause matched in the rest. For medusa-16502-lines both matched in 1 of 2, and only the cause in the other.

## Ablation: the list of causes

The v2-nomenu arm ran the same unguided task with feedback none, but the agent was not shown the list of causes and named only a file. It is compared with the v2 arm with feedback none on the two race scenarios, with the same two numbers per scenario.

One trial, nomenu-none-8, was stopped by our safety rule after one cart became two orders in a single run, a failure outside the three scenarios. The trial was rerun from scratch. Later runs showed that this happens only with two servers and Medusa's default in-memory lock, which Medusa documents as meant for development only. [RESULTS.md](../../RESULTS.md#one-cart-two-orders) has the numbers, and the stopped record is published in [stopped/scale-10-nomenu-none-8](stopped/scale-10-nomenu-none-8/).

The comparison is counted both ways: with the rerun trial, and with the stopped trial counted as a miss.

| Test scenario | v2, feedback none | v2-nomenu, with the rerun | v2-nomenu, stopped trial as a miss |
|---|---|---|---|
| medusa-17032-last-unit | 7 of 10, median 33 | 9 of 10, median 33 | 8 of 10, median 33 |
| medusa-17032-counter | 7 of 10, median 33 | 9 of 10, median 33 | 8 of 10, median 33 |

Without the list of causes the agent reproduced the two race scenarios in more trials, at the same median, counted either way. It never tested two cart lines that use the same stock, so it never reproduced medusa-16502-lines (0 of 10, against 3 of 10 with the list) or all three scenarios in one trial. The file it named matched the answer key in 8 of its 9 reproductions of each race scenario. With 10 trials per arm, the difference is not called significant.

## Lessons

- The automatic review after a plan tries one fix at a time: the fix from pull request [#17420](https://github.com/medusajs/medusa/pull/17420), then Redis locking. That cannot clear a scenario that has both bugs, so on random seed 10 it found `no_oversell` still failing with each one, in 25 and 13 of 60 runs, and stopped the plan. Random seed 4 had the same kind of scenario: several carts on two servers, some with two lines that use the same stock. Trying both fixes together, the #16502 fix from pull request [#16961](https://github.com/medusajs/medusa/pull/16961) with Redis locking, cleared both seeds: `no_oversell` failed in 0 of 60 runs for each, against 60 of 60 and 58 of 60 on plain Medusa. Both seeds are published with these runs in their `review/` folders, labeled "covered by #16502 and #17032 together".

## What is still small about the sample

- 10 trials per method. A difference of a few trials out of 10 can come from chance. The [statistics tests](../../RESULTS.md#statistics-run-after-the-fact), chosen after seeing the data, find that only the grid's lead on medusa-16502-lines and on all three in one trial passes a standard test.
- One model, `claude-haiku-5-5`, in every arm except sonnet-none of [plan followups-1](#plan-followups-1), one Medusa version, 2.22.0, and three test scenarios from two public bugs.
- Trials 1 to 3 of the four columns ran earlier, in separate sessions, on the same images, Oversold commit and prompts as trials 4 to 10.

## Plan followups-1

The [plan file](plans/followups-1.yaml) ran 23 unguided trials with feedback none in a fixed order, each with a budget of 300 runs, 30 attempts, 100 turns and $1. Its tests were written into the plan file and pushed before its first trial. The results and the tests are in [RESULTS.md](../../RESULTS.md#6-follow-up-experiments-the-whole-budget-and-a-bigger-model), and more about the plan is in [followups-1/](followups-1/).

- **budget-none** ran `claude-haiku-5-5` on prompt version v2-budget for 3 trials and was then closed: each gate answer used up a turn, and in 2 of its 3 trials the agent reached the 100-turn cap while it waited for run results.
- **budget2-none** ran `claude-haiku-5-5` on prompt version v2-budget2, which replaced v2-budget.
- **sonnet-none** ran `claude-sonnet-5-5` on prompt version v2.

The 23 trials used 3,691 runs and cost $4.8807. Only the Sonnet trials all ended with the agent calling finish. Of the budget2-none trials, 1 called finish, 5 ended after 15 gate answers and 4 ended when the model stopped replying with a tool call once 60 or fewer runs were left. The 3 budget-none trials all ended without finish. Claims: 3 backed by a violation and none not backed for budget2-none, 8 backed and 1 not backed for sonnet-none. Three trials, sonnet-none-3, sonnet-none-5 and budget2-none-6, were held for one cart becoming two orders on two servers with in-memory locking, reviewed by hand and published with their review runs. sonnet-none-3 and sonnet-none-4 were each run again from scratch, as [followups-1/](followups-1/) explains.

| Trial | Model | Prompts | Ended | Gate answers | Turns | Attempts (refused) | Runs | Reproduced (run of first reproduction) | Claims backed by a violation / not | Expected check failed | Dollars |
|---|---|---|---|---|---|---|---|---|---|---|---|
| [budget-none-1](followups-1/budget-none-1/) | claude-haiku-5-5 | v2-budget | the model stopped without calling finish | 17 | 68 | 16 (0) | 265 | medusa-16502-lines (run 23), medusa-17032-counter (run 66), medusa-17032-last-unit (run 66) | no finish | 8 of 16 | 0.0632 |
| [budget-none-2](followups-1/budget-none-2/) | claude-haiku-5-5 | v2-budget | the model stopped without calling finish | 72 | 100 | 6 (0) | 119 | medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | no finish | 3 of 6 | 0.0579 |
| [budget-none-3](followups-1/budget-none-3/) | claude-haiku-5-5 | v2-budget | the model stopped without calling finish | 77 | 100 | 7 (0) | 129 | medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | no finish | 4 of 7 | 0.0525 |
| [budget2-none-1](followups-1/budget2-none-1/) | claude-haiku-5-5 | v2-budget2 | stopped after 15 gate answers | 15 | 48 | 8 (0) | 126 | medusa-16502-lines (run 76), medusa-17032-counter (run 43), medusa-17032-last-unit (run 43) | no finish | 2 of 8 | 0.0426 |
| [budget2-none-2](followups-1/budget2-none-2/) | claude-haiku-5-5 | v2-budget2 | the model stopped without calling finish | 12 | 37 | 13 (0) | 248 | medusa-16502-lines (run 23), medusa-17032-counter (run 66), medusa-17032-last-unit (run 66) | no finish | 5 of 13 | 0.0327 |
| [budget2-none-3](followups-1/budget2-none-3/) | claude-haiku-5-5 | v2-budget2 | the model stopped without calling finish | 13 | 46 | 15 (0) | 268 | medusa-16502-lines (run 192), medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | no finish | 6 of 15 | 0.0428 |
| [budget2-none-4](followups-1/budget2-none-4/) | claude-haiku-5-5 | v2-budget2 | finished by the model | 9 | 28 | 11 (0) | 241 | medusa-16502-lines (run 165), medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | 3 / 0 | 6 of 11 | 0.0264 |
| [budget2-none-5](followups-1/budget2-none-5/) | claude-haiku-5-5 | v2-budget2 | the model stopped without calling finish | 11 | 46 | 15 (0) | 281 | medusa-16502-lines (run 56), medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | no finish | 5 of 15 | 0.0395 |
| [budget2-none-6](followups-1/budget2-none-6/) | claude-haiku-5-5 | v2-budget2 | the model stopped without calling finish | 13 | 59 | 15 (0) | 246 | medusa-16502-lines (run 99), medusa-17032-counter (run 43), medusa-17032-last-unit (run 43) | no finish | 6 of 15 | 0.0538 |
| [budget2-none-7](followups-1/budget2-none-7/) | claude-haiku-5-5 | v2-budget2 | stopped after 15 gate answers | 15 | 43 | 13 (0) | 235 | medusa-16502-lines (run 192), medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | no finish | 5 of 13 | 0.0381 |
| [budget2-none-8](followups-1/budget2-none-8/) | claude-haiku-5-5 | v2-budget2 | stopped after 15 gate answers | 15 | 57 | 10 (0) | 149 | medusa-17032-counter (run 43), medusa-17032-last-unit (run 43) | no finish | 3 of 10 | 0.0464 |
| [budget2-none-9](followups-1/budget2-none-9/) | claude-haiku-5-5 | v2-budget2 | stopped after 15 gate answers | 15 | 31 | 6 (0) | 106 | medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | no finish | 2 of 6 | 0.0281 |
| [budget2-none-10](followups-1/budget2-none-10/) | claude-haiku-5-5 | v2-budget2 | stopped after 15 gate answers | 15 | 40 | 7 (0) | 142 | medusa-17032-counter (run 23), medusa-17032-last-unit (run 56) | no finish | 4 of 7 | 0.0292 |
| [sonnet-none-1](followups-1/sonnet-none-1/) | claude-sonnet-5-5 | v2 | finished by the model | not gated | 25 | 5 (0) | 119 | medusa-16502-lines (run 23), medusa-17032-counter (run 76), medusa-17032-last-unit (run 76) | 2 / 0 | 3 of 5 | 0.5593 |
| [sonnet-none-2](followups-1/sonnet-none-2/) | claude-sonnet-5-5 | v2 | finished by the model | not gated | 20 | 5 (0) | 119 | medusa-16502-lines (run 23), medusa-17032-counter (run 86), medusa-17032-last-unit (run 86) | 0 / 0 | 3 of 5 | 0.3584 |
| [sonnet-none-3](followups-1/sonnet-none-3/) | claude-sonnet-5-5 | v2 | finished by the model | not gated | 19 | 5 (0) | 109 | medusa-16502-lines (run 23), medusa-17032-counter (run 66), medusa-17032-last-unit (run 66) | 1 / 0 | 3 of 5 | 0.3023 |
| [sonnet-none-4](followups-1/sonnet-none-4/) | claude-sonnet-5-5 | v2 | finished by the model | not gated | 29 | 7 (7) | 0 | none | 0 / 0 | 0 of 0 | 0.4662 |
| [sonnet-none-5](followups-1/sonnet-none-5/) | claude-sonnet-5-5 | v2 | finished by the model | not gated | 26 | 5 (0) | 132 | medusa-16502-lines (run 23), medusa-17032-counter (run 66), medusa-17032-last-unit (run 66) | 2 / 0 | 4 of 5 | 0.6388 |
| [sonnet-none-6](followups-1/sonnet-none-6/) | claude-sonnet-5-5 | v2 | finished by the model | not gated | 21 | 4 (0) | 112 | medusa-16502-lines (run 23), medusa-17032-counter (run 66), medusa-17032-last-unit (run 66) | 0 / 0 | 3 of 4 | 0.4127 |
| [sonnet-none-7](followups-1/sonnet-none-7/) | claude-sonnet-5-5 | v2 | finished by the model | not gated | 23 | 5 (0) | 132 | medusa-16502-lines (run 23), medusa-17032-counter (run 66), medusa-17032-last-unit (run 66) | 1 / 0 | 3 of 5 | 0.3696 |
| [sonnet-none-8](followups-1/sonnet-none-8/) | claude-sonnet-5-5 | v2 | finished by the model | not gated | 22 | 7 (0) | 152 | medusa-16502-lines (run 33), medusa-17032-counter (run 76), medusa-17032-last-unit (run 76) | 1 / 1 | 4 of 7 | 0.3747 |
| [sonnet-none-9](followups-1/sonnet-none-9/) | claude-sonnet-5-5 | v2 | finished by the model | not gated | 19 | 5 (0) | 109 | medusa-16502-lines (run 23), medusa-17032-counter (run 76), medusa-17032-last-unit (run 76) | 1 / 0 | 3 of 5 | 0.3726 |
| [sonnet-none-10](followups-1/sonnet-none-10/) | claude-sonnet-5-5 | v2 | finished by the model | not gated | 25 | 7 (0) | 152 | medusa-16502-lines (run 23), medusa-17032-counter (run 66), medusa-17032-last-unit (run 66) | 0 / 0 | 4 of 7 | 0.4729 |

## Plan scale-10

The [plan file](plans/scale-10.yaml) ran 38 unguided trials in a fixed order with `claude-haiku-5-5`, each with a budget of 300 runs and $1: trials 4 to 10 of the grid, random and the two v2 arms, and trials 1 to 10 of the v2-nomenu arm. The plan file and the prompts were committed before its first trial ran.

The 24 agent trials below used 844 runs and cost $0.1694. 21 ended with the agent calling finish, and 3, all on v2-nomenu, with the model stopping without calling finish. Their claims: 9 backed by a violation and 1 not backed. The 14 baseline trials are listed in [../README.md](../README.md#baselines).

| Trial | Prompts | Feedback | Turns | Attempts (refused) | Runs | Reproduced (run of first reproduction) | Claims backed by a violation / not | Expected check failed | Dollars |
|---|---|---|---|---|---|---|---|---|---|
| [unguided-none-4](scale-10/unguided-none-4/) | v2 | none | 11 | 1 (0) | 10 | none | 0 / 0 | 0 of 1 | 0.0044 |
| [unguided-none-5](scale-10/unguided-none-5/) | v2 | none | 11 | 2 (0) | 43 | medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | 0 / 0 | 1 of 2 | 0.0058 |
| [unguided-none-6](scale-10/unguided-none-6/) | v2 | none | 11 | 1 (0) | 33 | medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | 1 / 0 | 1 of 1 | 0.0046 |
| [unguided-none-7](scale-10/unguided-none-7/) | v2 | none | 16 | 2 (0) | 20 | none | 0 / 0 | 0 of 2 | 0.0081 |
| [unguided-none-8](scale-10/unguided-none-8/) | v2 | none | 7 | 2 (0) | 73 | medusa-16502-lines (run 63), medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | 0 / 0 | 2 of 2 | 0.0046 |
| [unguided-none-9](scale-10/unguided-none-9/) | v2 | none | 14 | 2 (0) | 43 | medusa-17032-counter (run 43), medusa-17032-last-unit (run 43) | 0 / 0 | 1 of 2 | 0.0077 |
| [unguided-none-10](scale-10/unguided-none-10/) | v2 | none | 15 | 1 (0) | 10 | none | 0 / 0 | 0 of 1 | 0.0105 |
| [unguided-history-4](scale-10/unguided-history-4/) | v2 | history | 24 | 1 (0) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0173 |
| [unguided-history-5](scale-10/unguided-history-5/) | v2 | history | 7 | 1 (0) | 33 | medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | 1 / 0 | 1 of 1 | 0.0028 |
| [unguided-history-6](scale-10/unguided-history-6/) | v2 | history | 8 | 1 (0) | 33 | medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | 1 / 0 | 1 of 1 | 0.0025 |
| [unguided-history-7](scale-10/unguided-history-7/) | v2 | history | 11 | 1 (0) | 40 | medusa-17032-counter (run 40), medusa-17032-last-unit (run 40) | 1 / 0 | 1 of 1 | 0.0035 |
| [unguided-history-8](scale-10/unguided-history-8/) | v2 | history | 10 | 3 (0) | 30 | none | 0 / 0 | 0 of 3 | 0.0041 |
| [unguided-history-9](scale-10/unguided-history-9/) | v2 | history | 9 | 2 (0) | 43 | medusa-17032-counter (run 43), medusa-17032-last-unit (run 43) | 1 / 0 | 1 of 2 | 0.0037 |
| [unguided-history-10](scale-10/unguided-history-10/) | v2 | history | 13 | 1 (0) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0081 |
| [nomenu-none-1](scale-10/nomenu-none-1/) | v2-nomenu | none | 13 | 1 (0) | 33 | medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | no finish | 1 of 1 | 0.0096 |
| [nomenu-none-2](scale-10/nomenu-none-2/) | v2-nomenu | none | 15 | 2 (0) | 43 | medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | 0 / 0 | 1 of 2 | 0.0081 |
| [nomenu-none-3](scale-10/nomenu-none-3/) | v2-nomenu | none | 9 | 1 (0) | 33 | medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | 0 / 0 | 1 of 1 | 0.0033 |
| [nomenu-none-4](scale-10/nomenu-none-4/) | v2-nomenu | none | 10 | 1 (0) | 33 | medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | 0 / 0 | 1 of 1 | 0.0056 |
| [nomenu-none-5](scale-10/nomenu-none-5/) | v2-nomenu | none | 11 | 2 (0) | 43 | medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | no finish | 2 of 2 | 0.0051 |
| [nomenu-none-6](scale-10/nomenu-none-6/) | v2-nomenu | none | 13 | 2 (0) | 20 | none | 0 / 1 | 1 of 2 | 0.0097 |
| [nomenu-none-7](scale-10/nomenu-none-7/) | v2-nomenu | none | 13 | 1 (0) | 33 | medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | 0 / 0 | 1 of 1 | 0.0083 |
| [nomenu-none-8](scale-10/nomenu-none-8/) | v2-nomenu | none | 12 | 2 (0) | 43 | medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | 1 / 0 | 1 of 2 | 0.0078 |
| [nomenu-none-9](scale-10/nomenu-none-9/) | v2-nomenu | none | 15 | 2 (0) | 43 | medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | 1 / 0 | 1 of 2 | 0.0136 |
| [nomenu-none-10](scale-10/nomenu-none-10/) | v2-nomenu | none | 13 | 2 (0) | 43 | medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | no finish | 1 of 2 | 0.0104 |

## Plan unguided-haiku-1

The [plan file](plans/unguided-haiku-1.yaml) asked for 6 unguided trials with `claude-haiku-5-5`, 3 with feedback none and 3 with feedback history, on prompt version v2. All 6 ended with the agent calling finish. Together they used 314 runs and cost $0.0479. They are trials 1 to 3 of the two v2 arms in the headline above.

| Trial | Feedback | Turns | Attempts (refused) | Runs | Reproduced (run of first reproduction) | Claims backed by a violation / not | Expected check failed | Dollars |
|---|---|---|---|---|---|---|---|---|
| [unguided-none-1](unguided-haiku-1/unguided-none-1/) | none | 10 | 2 (0) | 66 | medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | 0 / 0 | 2 of 2 | 0.0068 |
| [unguided-none-2](unguided-haiku-1/unguided-none-2/) | none | 10 | 2 (0) | 66 | medusa-16502-lines (run 56), medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | 1 / 0 | 2 of 2 | 0.0039 |
| [unguided-none-3](unguided-haiku-1/unguided-none-3/) | none | 15 | 2 (0) | 66 | medusa-16502-lines (run 56), medusa-17032-counter (run 33), medusa-17032-last-unit (run 33) | 0 / 0 | 2 of 2 | 0.0095 |
| [unguided-history-1](unguided-haiku-1/unguided-history-1/) | history | 11 | 3 (0) | 53 | medusa-17032-counter (run 53), medusa-17032-last-unit (run 53) | 1 / 0 | 1 of 3 | 0.0062 |
| [unguided-history-2](unguided-haiku-1/unguided-history-2/) | history | 14 | 1 (0) | 23 | medusa-17032-counter (run 23) | 1 / 0 | 1 of 1 | 0.0107 |
| [unguided-history-3](unguided-haiku-1/unguided-history-3/) | history | 15 | 4 (1) | 40 | none | 1 / 0 | 1 of 3 | 0.0108 |

The three trials with feedback history were held and reviewed before they were published. In two of them, one check failed in a single run and not again in that attempt's scoring runs, so the score could not pin the failure on one case. For each of these two, the exact scenario of that attempt was run again 60 times on plain Medusa 2.22.0, 60 times with the fix from pull request #17420, and 60 times with Medusa's Redis locking. These review runs were made after the trial, only to decide whether to publish it. They do not change the trial's score or its runs to first reproduction.

| Trial | Scenario | Check | Plain Medusa | With the #17420 fix | With Redis locking |
|---|---|---|---|---|---|
| unguided-history-2 | 12 carts with one OVS-PIECE each and 10 WIDGET in stock; every cart is completed twice at the same moment, once on each of two servers | no_oversell | 3 of 60 | 0 of 60 | 0 of 60 |
| unguided-history-3 | 3 carts with one OVS-SOLO each on two servers, SOLO stock raised to 5 before the race, all completed together | reserved_matches_reservations | 1 of 60 | 0 of 60 | 0 of 60 |

No other check failed on the fix or with Redis locking in these runs. Both failures are labeled "covered by #17032, rare in this scenario": two servers with in-memory locking, which issue #17032 describes. Each trial's review runs are in its `review/` folder, with a `review.json` summary.

## Plan guided-haiku-2

The [plan file](plans/guided-haiku-2.yaml) reran the #17032 guided cells on prompt version v2: 3 trials with feedback none and 3 with feedback history. The #16502 cells were not rerun, because every v1 trial there already reproduced the bug at run 23. All 6 trials ended with the agent calling finish, used 281 runs and cost $0.0216.

| Trial | Feedback | Turns | Attempts (refused) | Runs | Reproduced (run of first reproduction) | Claims backed by a violation / not | Expected check failed | Dollars |
|---|---|---|---|---|---|---|---|---|
| [17032-none-1](guided-haiku-2/17032-none-1/) | none | 6 | 1 (0) | 33 | medusa-16502-lines (run 23) | 0 / 0 | 1 of 1 | 0.0035 |
| [17032-none-2](guided-haiku-2/17032-none-2/) | none | 7 | 2 (1) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0031 |
| [17032-none-3](guided-haiku-2/17032-none-3/) | none | 8 | 1 (0) | 33 | medusa-16502-lines (run 23) | 0 / 0 | 1 of 1 | 0.0033 |
| [17032-history-1](guided-haiku-2/17032-history-1/) | history | 9 | 4 (1) | 76 | medusa-16502-lines (run 23), medusa-17032-counter (run 76), medusa-17032-last-unit (run 76) | 2 / 0 | 2 of 3 | 0.0046 |
| [17032-history-2](guided-haiku-2/17032-history-2/) | history | 8 | 2 (1) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0036 |
| [17032-history-3](guided-haiku-2/17032-history-3/) | history | 6 | 2 (0) | 73 | medusa-16502-lines (run 30), medusa-17032-counter (run 73), medusa-17032-last-unit (run 73) | 2 / 0 | 2 of 2 | 0.0034 |

Given the #17032 bug report, in how many of 3 trials each test scenario was reproduced:

| Test scenario | v1, none | v2, none | v1, history | v2, history |
|---|---|---|---|---|
| medusa-17032-last-unit | 0 of 3 | 0 of 3 | 0 of 3 | 2 of 3 |
| medusa-17032-counter | 0 of 3 | 0 of 3 | 0 of 3 | 2 of 3 |
| medusa-16502-lines | 3 of 3 | 3 of 3 | 2 of 3 | 3 of 3 |

## Plan guided-haiku-1

The [plan file](plans/guided-haiku-1.yaml) asked for 12 guided trials with the model `claude-haiku-5-5`: the bug reports for Medusa issues [#16502](https://github.com/medusajs/medusa/issues/16502) and [#17032](https://github.com/medusajs/medusa/issues/17032), each with feedback none and history, 3 trials each. It ran on prompt version v1. The plan, the code and the prompts were committed and pushed before the first trial ran.

All 12 trials ended with the agent calling finish. Together they used 387 runs and cost $0.0366.

| Trial | Bug report | Feedback | Turns | Attempts (refused) | Runs | Reproduced (run of first reproduction) | Claims backed by a violation / not | Expected check failed | Dollars |
|---|---|---|---|---|---|---|---|---|---|
| [16502-none-1](guided-haiku-1/16502-none-1/) | #16502 | none | 4 | 1 (0) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0028 |
| [16502-none-2](guided-haiku-1/16502-none-2/) | #16502 | none | 4 | 1 (0) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0027 |
| [16502-none-3](guided-haiku-1/16502-none-3/) | #16502 | none | 4 | 1 (0) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0026 |
| [16502-history-1](guided-haiku-1/16502-history-1/) | #16502 | history | 4 | 1 (0) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0019 |
| [16502-history-2](guided-haiku-1/16502-history-2/) | #16502 | history | 4 | 1 (0) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0018 |
| [16502-history-3](guided-haiku-1/16502-history-3/) | #16502 | history | 9 | 1 (0) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0070 |
| [17032-none-1](guided-haiku-1/17032-none-1/) | #17032 | none | 6 | 1 (0) | 40 | medusa-16502-lines (run 30) | 1 / 0 | 1 of 1 | 0.0035 |
| [17032-none-2](guided-haiku-1/17032-none-2/) | #17032 | none | 5 | 1 (0) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0030 |
| [17032-none-3](guided-haiku-1/17032-none-3/) | #17032 | none | 6 | 1 (0) | 40 | medusa-16502-lines (run 30) | 1 / 0 | 1 of 1 | 0.0035 |
| [17032-history-1](guided-haiku-1/17032-history-1/) | #17032 | history | 6 | 2 (1) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0029 |
| [17032-history-2](guided-haiku-1/17032-history-2/) | #17032 | history | 5 | 1 (0) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0024 |
| [17032-history-3](guided-haiku-1/17032-history-3/) | #17032 | history | 5 | 1 (0) | 10 | none | 0 / 0 | 0 of 1 | 0.0025 |

"Run of first reproduction" counts the runs the trial had used when the scenario was first reproduced. Every reproduced scenario above came with the file and the cause in its answer key.

What the table shows:

- **#16502 report**: all 6 trials reproduced medusa-16502-lines with their first attempt. Each test used one cart whose two lines together need more of one item than is in stock.
- **#17032 report**: 5 of 6 trials reproduced medusa-16502-lines, the other bug, and no trial reproduced either #17032 scenario. Every one of these tests used a single server, while the #17032 scenarios need two servers sharing one database. In all 6 trials the agent named the inventory module file and the per-line cause, which the #17032 report itself mentions when it refers to #16502.
- **Claims**: 11 claims were backed by a violation and none was not, in both feedback modes. One trial made no claim.
- **Expected check**: in 11 of 12 attempts that ran, the check the agent expected to fail did fail.

## Guided results are not a fair comparison

The guided results are not a fair comparison with the two simple methods, because the agent was given the public bug report and the simple methods were not. The fair comparison is the unguided headline above.

## What each trial folder holds

- `score.json`: the trial's summary.
- `attempts.json` and `attempts/`: each attempt as submitted and as run, with its guess and results.
- `claims.json`: the agent's final summary and its claims. Each claim is marked backed by a violation or not, and holds the attempt's saved prediction next to the claim's own diagnosis after results, graded on its own.
- `ledger.jsonl`: the trial's ledger lines, including each model call's tokens and cost.
- `transcript.jsonl.gz`: everything the model was shown and wrote, with anything that looks like a key masked. The transcripts quote Medusa source code from files under the [MIT license](https://github.com/medusajs/medusa/blob/v2.22.0/LICENSE). None of them quotes Medusa's Enterprise Edition files, which are under a different license.
- `runs/`: every Oversold run with its full history. CI rechecks each one with `oversold check --verify`.
- `review/`: only in a trial that was held and published after a review. It holds the extra runs, and `review/review.json` gives each set's runs and the failures of every check. These runs do not change the trial's score.

The [pilot](pilot/) is an earlier development run with the same layout. It is not counted.
