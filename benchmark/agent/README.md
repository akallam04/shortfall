# Agent trials

This page explains, in plain words, what the AI agent has done so far, and lists every trial it has run.

## What a trial is

A trial gives the agent one task and a fixed budget of runs, attempts, turns and dollars. Every trial so far had at most 300 runs and $1. Trials on prompt version v1 also had at most 12 attempts and 60 turns, and trials on v2 at most 30 attempts and 100 turns. A turn is one reply from the AI model. A run is one go of a test on a fresh private copy of the shop.

During a trial the agent reads Medusa's source code and then submits attempts. Each attempt is a small test scenario plus a guess: the source file it thinks holds the problem, one cause from a fixed list, and the one check it expects to fail. The guess is saved before the test runs, so it cannot be changed once the result is known. When the agent is done, it calls finish and lists its claims.

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
- **Located**: the file and the cause the agent named match the answer key for that test scenario.

## Claims

At the end, the agent lists claims: the attempts it believes found a real problem, each with a file and a cause. A claim is **backed** when that attempt had a violation on plain Medusa. It is **unbacked** when that attempt had no violation, was refused or never ran.

In the none mode the agent never sees any results, so an unbacked claim there is a false alarm. In the history mode it sees the results, so its claims should be backed.

## Prompt versions

Everything the agent is shown, and the settings of its loop, are fixed by one hash before any trial of a plan runs. Each plan folder holds the hash it used.

- **v1** ([hash](guided-haiku-1/prompts.sha256)) was used by guided-haiku-1.
- **v2** ([hash](prompts.sha256)) is used by unguided-haiku-1 and guided-haiku-2.

v2 was written after the guided v1 results were known. The unguided trials ran only on v2. What changed from v1 to v2, and why:

- In the none feedback mode the agent no longer sees how many runs are left, only attempts and turns. On v1 the run count told it, indirectly, whether an attempt had found something, because an attempt that finds something gets extra runs to confirm it.
- The budget is now 300 runs, 30 attempts and 100 turns, so the run budget is the real limit, as it is for the two simple methods. The agent is told that the budget is for finding as many distinct problems as it can, and that one finding does not end the task.
- In guided trials the agent is told to check that its scenario matches the conditions the bug report describes before it claims the reported bug. On v1, given the #17032 report, the agent tested on one server, while that report describes two.
- Medusa's Enterprise Edition files are hidden from the agent's tools, because they are not under the MIT license.
- Old tool results are now shortened in batches every 6 turns instead of one per turn. This lets more of each request be read from the prompt cache, which costs less.

## Headline: unguided trials against the simple methods

Each cell says in how many of 3 trials the test scenario was reproduced, and the median runs to its first reproduction. All four methods had a budget of 300 runs per trial. The two simple methods are described in [../README.md](../README.md).

| Test scenario | Grid (no AI) | Random (no AI) | Agent, unguided, feedback none | Agent, unguided, feedback history |
|---|---|---|---|---|
| medusa-17032-last-unit | 3 of 3, median 81 | 3 of 3, median 117 | 3 of 3, median 33 | 1 of 3, at 53 |
| medusa-17032-counter | 3 of 3, median 39 | 3 of 3, median 42 | 3 of 3, median 33 | 2 of 3, median 38 |
| medusa-16502-lines | 3 of 3, median 29 | 1 of 3, at 51 | 2 of 3, median 56 | 0 of 3 |

This is a small sample: 3 trials per method. No difference in this table is called significant.

In the three unguided trials with feedback none, the agent named the file and the cause in the answer key every time it reproduced a #17032 scenario. When it reproduced medusa-16502-lines, the cause matched the answer key and the file did not. Each of these trials stopped on its own after 2 attempts and 66 of its 300 runs.

In the three unguided trials with feedback history, the cause matched the answer key every time a #17032 scenario was reproduced, and the file matched in one of the three reproductions. These trials stopped on their own after 23 to 53 runs.

## Plan unguided-haiku-1

The [plan file](plans/unguided-haiku-1.yaml) asked for 6 unguided trials with `claude-haiku-5-5`, 3 with feedback none and 3 with feedback history, on prompt version v2. All 6 ended with the agent calling finish. Together they used 314 runs and cost $0.0479.

| Trial | Feedback | Turns | Attempts (refused) | Runs | Reproduced (run of first reproduction) | Claims backed / unbacked | Expected check failed | Dollars |
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

| Trial | Feedback | Turns | Attempts (refused) | Runs | Reproduced (run of first reproduction) | Claims backed / unbacked | Expected check failed | Dollars |
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

| Trial | Bug report | Feedback | Turns | Attempts (refused) | Runs | Reproduced (run of first reproduction) | Claims backed / unbacked | Expected check failed | Dollars |
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
- **Claims**: 11 claims were backed and none was unbacked, in both feedback modes. One trial made no claim.
- **Expected check**: in 11 of 12 attempts that ran, the check the agent expected to fail did fail.

## Guided results are not a fair comparison

The guided results are not a fair comparison with the two simple methods, because the agent was given the public bug report and the simple methods were not. The fair comparison is the unguided headline above.

## What each trial folder holds

- `score.json`: the trial's summary.
- `attempts.json` and `attempts/`: each attempt as submitted and as run, with its guess and results.
- `claims.json`: the agent's final summary and its claims, each marked backed or unbacked.
- `ledger.jsonl`: the trial's ledger lines, including each model call's tokens and cost.
- `transcript.jsonl.gz`: everything the model was shown and wrote, with anything that looks like a key masked. The transcripts quote Medusa source code from files under the [MIT license](https://github.com/medusajs/medusa/blob/v2.22.0/LICENSE). None of them quotes Medusa's Enterprise Edition files, which are under a different license.
- `runs/`: every Oversold run with its full history. CI rechecks each one with `oversold check --verify`.

The [pilot](pilot/) is an earlier development run with the same layout. It is not counted.
