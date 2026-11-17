# Agent trials

This page explains, in plain words, what the AI agent has done so far, and lists every trial it has run.

## What a trial is

A trial gives the agent one task and a fixed budget: at most 300 runs, 12 attempts, 60 turns and $1. A turn is one reply from the AI model. A run is one go of a test on a fresh private copy of the shop.

During a trial the agent reads Medusa's source code and then submits attempts. Each attempt is a small test scenario plus a guess: the source file it thinks holds the problem, one cause from a fixed list, and the one check it expects to fail. The guess is saved before the test runs, so it cannot be changed once the result is known. When the agent is done, it calls finish and lists its claims.

## What guided means

In a guided trial the agent gets the public bug report for one known bug, like an open-book test. The report describes what goes wrong and often names the source file involved. So a guided trial shows whether the agent can turn a bug report into a test that reproduces the bug. It does not show whether the agent can find a bug on its own.

There are two feedback modes:

- **none**: after each attempt the agent only learns whether the attempt was accepted, and how many runs, attempts and turns it has left.
- **history**: it also sees, for the runs on plain Medusa, how often each check failed and a short summary of each run.

## The three results

Every attempt that runs gets three results:

- **Violation**: a check failed in at least one run on plain Medusa 2.22.0.
- **Reproduced**: the failure matches one of the benchmark's three test scenarios, and the same test passes on a copy of Medusa with the public fix for that bug.
- **Located**: the file and the cause the agent named match the answer key for that test scenario.

## Claims

At the end, the agent lists claims: the attempts it believes found a real problem, each with a file and a cause. A claim is **backed** when that attempt had a violation on plain Medusa. It is **unbacked** when that attempt had no violation, was refused or never ran.

In the none mode the agent never sees any results, so an unbacked claim there is a false alarm. In the history mode it sees the results, so its claims should be backed.

## Plan guided-haiku-1

The [plan file](plans/guided-haiku-1.yaml) asked for 12 guided trials with the model `claude-haiku-5-5`: the bug reports for Medusa issues [#16502](https://github.com/medusajs/medusa/issues/16502) and [#17032](https://github.com/medusajs/medusa/issues/17032), each with feedback none and history, 3 trials each. The plan, the code and the prompts were committed and pushed before the first trial ran. Everything the agent is shown is fixed by the hash in [prompts.sha256](prompts.sha256).

All 12 trials ended with the agent calling finish. Together they used 387 runs and cost $0.0366.

| Trial | Bug report | Feedback | Turns | Attempts (refused) | Runs | Reproduced (run of first reproduction) | Claims backed / unbacked | Expected check failed | Dollars |
|---|---|---|---|---|---|---|---|---|---|
| [16502-none-1](16502-none-1/) | #16502 | none | 4 | 1 (0) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0028 |
| [16502-none-2](16502-none-2/) | #16502 | none | 4 | 1 (0) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0027 |
| [16502-none-3](16502-none-3/) | #16502 | none | 4 | 1 (0) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0026 |
| [16502-history-1](16502-history-1/) | #16502 | history | 4 | 1 (0) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0019 |
| [16502-history-2](16502-history-2/) | #16502 | history | 4 | 1 (0) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0018 |
| [16502-history-3](16502-history-3/) | #16502 | history | 9 | 1 (0) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0070 |
| [17032-none-1](17032-none-1/) | #17032 | none | 6 | 1 (0) | 40 | medusa-16502-lines (run 30) | 1 / 0 | 1 of 1 | 0.0035 |
| [17032-none-2](17032-none-2/) | #17032 | none | 5 | 1 (0) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0030 |
| [17032-none-3](17032-none-3/) | #17032 | none | 6 | 1 (0) | 40 | medusa-16502-lines (run 30) | 1 / 0 | 1 of 1 | 0.0035 |
| [17032-history-1](17032-history-1/) | #17032 | history | 6 | 2 (1) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0029 |
| [17032-history-2](17032-history-2/) | #17032 | history | 5 | 1 (0) | 33 | medusa-16502-lines (run 23) | 1 / 0 | 1 of 1 | 0.0024 |
| [17032-history-3](17032-history-3/) | #17032 | history | 5 | 1 (0) | 10 | none | 0 / 0 | 0 of 1 | 0.0025 |

"Run of first reproduction" counts the runs the trial had used when the scenario was first reproduced. Every reproduced scenario above came with the file and the cause in its answer key.

What the table shows:

- **#16502 report**: all 6 trials reproduced medusa-16502-lines with their first attempt. Each test used one cart whose two lines together need more of one item than is in stock.
- **#17032 report**: 5 of 6 trials reproduced medusa-16502-lines, the other bug, and no trial reproduced either #17032 scenario. Every one of these tests used a single server, while the #17032 scenarios need two servers sharing one database. In all 6 trials the agent named the inventory module file and the per-line cause, which the #17032 report itself mentions when it refers to #16502.
- **Claims**: 11 claims were backed and none was unbacked, in both feedback modes. One trial made no claim.
- **Expected check**: in 11 of 12 attempts that ran, the check the agent expected to fail did fail.

## Not a fair comparison yet

These guided results are not a fair comparison with the no-model baselines in [../README.md](../README.md). The agent was given the public bug report, and the baselines were not. The fair comparison will come from unguided trials, where the agent gets no bug report. Those have not run yet.

## What each trial folder holds

- `score.json`: the trial's summary.
- `attempts.json` and `attempts/`: each attempt as submitted and as run, with its guess and results.
- `claims.json`: the agent's final summary and its claims, each marked backed or unbacked.
- `ledger.jsonl`: the trial's ledger lines, including each model call's tokens and cost.
- `transcript.jsonl.gz`: everything the model was shown and wrote, with anything that looks like a key masked. The transcripts quote Medusa source code from files under the [MIT license](https://github.com/medusajs/medusa/blob/v2.22.0/LICENSE). None of them quotes Medusa's Enterprise Edition files, which are under a different license.
- `runs/`: every Oversold run with its full history. CI rechecks each one with `oversold check --verify`.

The [pilot](pilot/) is an earlier development run with the same layout. It is not counted.
