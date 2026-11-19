# Results

This page explains what Shortfall found, in plain words. Every table here is rebuilt from the saved data by a test, and the test fails if any number in it changes.

## 1. In one minute

- We asked whether a cheap AI agent that reads a shop's code can find real checkout bugs faster than two simple searches that use no AI, with the same budget of 300 test runs.
- The simple fixed-list search found all three known bug scenarios in every one of its 10 tries. The agent found all three in at most 3 of 10 tries.
- When the agent found the "last item sold twice" scenario, it found it fast: a median of 33 runs, against 58.5 for the fixed list. On the other two-shoppers scenario, the fixed list tied it at 33.
- The agent stopped early, after a median of 33 to 43 of its 300 runs, so it rarely went on to look for the third scenario.
- Showing the agent its test results made it do worse. Hiding its list of likely causes did not hurt on the two two-shoppers scenarios.
- One agent try cost under 2 US cents and took about 4 minutes. Ten tries per method is still a small sample.

## 2. The question

Can a cheap AI agent that reads the code find real checkout race bugs faster than simple searches, with the same run budget and a checker it can't change?

A race bug is a bug that only shows up when two or more shoppers act at the same moment.

## 3. How the test works

**The shop software.** We tested Medusa 2.22.0, an open-source online shop engine. Every test ran on a fresh private copy of the shop on one computer, never on a real shop.

**The three known bug scenarios.** The benchmark uses three test scenarios built from two bugs that were already public:

- **Last unit sold twice** ([#17032](https://github.com/medusajs/medusa/issues/17032)): two shoppers buy the last item through two servers at once, and both purchases go through.
- **Reserved count goes wrong** ([#17032](https://github.com/medusajs/medusa/issues/17032)): the shop's count of stock set aside for orders loses updates when two servers work at once.
- **Two cart lines oversold** ([#16502](https://github.com/medusajs/medusa/issues/16502)): one cart has two lines that use the same stock, and the shop checks each line alone.

A scenario is a small test file: which items are in stock, which shoppers there are, and when they press Buy. In the tables below the three scenarios are called `medusa-17032-last-unit`, `medusa-17032-counter` and `medusa-16502-lines`.

**What "reproduced" means.** A run is one go of a test on a fresh copy of the shop. A scenario counts as reproduced when a test breaks the shop's rule on plain Medusa, and the same test passes on a copy of Medusa with the public fix for that bug: pull request [#17420](https://github.com/medusajs/medusa/pull/17420) for #17032 and pull request [#16961](https://github.com/medusajs/medusa/pull/16961) for #16502.

**The checker.** Every run goes through [Oversold](https://github.com/akallam04/oversold), a separate tool pinned to one public version. It starts the shop, sends the purchases, and checks five rules, such as "never sell more than you have". The agent can only write test files. It cannot change the checker, the rules or the answers.

**The budget.** A trial is one try of one method from scratch. Every trial had at most 300 runs.

**The five ways we searched**, 10 trials each:

- **Grid**: a fixed list of 32 test shapes, in a different shuffled order each trial. It was designed knowing what these bugs look like.
- **Random**: tests drawn at random from the same kinds of settings.
- **Agent, no feedback**: the AI model Claude Haiku 5.5 reads the code and writes tests. After each test it only learns whether the test was accepted.
- **Agent, with feedback**: the same, but it also sees how often each rule broke in its tests.
- **Agent, no cause list**: the same as no feedback, but without the list of likely causes it picks from. This tests whether that list helps.

**How we count speed.** "Runs to first reproduction" is how many runs a trial had used when it first reproduced a scenario. The median is the middle value of the 10 trials. A trial that missed counts as over 300 runs, so if half or more of the trials missed, the median is "over 300".

## 4. Results

### How often and how fast each method reproduced each scenario

Each cell says in how many of 10 trials the scenario was reproduced, and the median runs to its first reproduction. Data: [grid and random](benchmark/baselines/2004ed5/), [agent trials 1 to 3](benchmark/agent/unguided-haiku-1/), [agent trials 4 to 10 and the no cause list trials](benchmark/agent/scale-10/).

| Test scenario | Grid | Random | Agent, no feedback | Agent, with feedback | Agent, no cause list |
|---|---|---|---|---|---|
| medusa-17032-last-unit | 10 of 10, median 58.5 | 9 of 10, median 110 | 7 of 10, median 33 | 5 of 10, median over 300 | 9 of 10, median 33 |
| medusa-17032-counter | 10 of 10, median 33 | 10 of 10, median 46.5 | 7 of 10, median 33 | 6 of 10, median 48 | 9 of 10, median 33 |
| medusa-16502-lines | 10 of 10, median 54 | 7 of 10, median 135.5 | 3 of 10, median over 300 | 2 of 10, median over 300 | 0 of 10, median over 300 |
| All three in one trial | 10 of 10 | 6 of 10 | 3 of 10 | 0 of 10 | 0 of 10 |

When a test finds a two-servers bug on its first try, the scoring needs 33 runs to confirm it: 3 first runs, 10 more runs, and 10 runs on each of two fixed copies. That is why so many cells say 33.

### Cost and time per trial

Data: the same folders as above. Minutes are the time from a trial's start to its end. The two simple methods use no AI, so they cost nothing to run.

| Method | Trials | Median runs used | Median minutes per trial | Median dollars per trial | Total dollars |
|---|---|---|---|---|---|
| Grid | 10 | 297.5 | 34 | 0 | 0 |
| Random | 10 | 299.5 | 43 | 0 | 0 |
| Agent, no feedback | 10 | 43 | 4.2 | 0.0063 | 0.0659 |
| Agent, with feedback | 10 | 33 | 3.5 | 0.0052 | 0.0698 |
| Agent, no cause list | 10 | 38 | 3.9 | 0.0082 | 0.0816 |

The simple methods always used their whole budget. The agent stopped on its own long before it, and used at most 73 runs in any unguided trial.

### Claims

At the end of a trial the agent lists its claims: the tests it believes found a real problem. A claim is **backed** when that test really broke a rule on plain Medusa, and **unbacked** when it did not. An unbacked claim is a false alarm. Data: [agent trials 1 to 3](benchmark/agent/unguided-haiku-1/), [agent trials 4 to 10](benchmark/agent/scale-10/).

| Method | Trials | Trials that called finish | Claims backed | Claims unbacked |
|---|---|---|---|---|
| Agent, no feedback | 10 | 10 | 2 | 0 |
| Agent, with feedback | 10 | 10 | 9 | 0 |
| Agent, no cause list | 10 | 7 | 2 | 1 |

"Called finish" means the agent ended the trial itself and listed its claims. In three trials without the cause list, the model stopped replying with a tool call before it did that.

### Did it name the right place?

With every test the agent names the source file it suspects and, except without the cause list, one cause from a fixed list. For each trial that reproduced a scenario, this table counts how often the file and the cause matched the answer key. Data: the agent folders above and the [answer keys](benchmark/cases/).

| Method | Test scenario | Trials that reproduced it | File matched | Cause matched |
|---|---|---|---|---|
| Agent, no feedback | medusa-17032-last-unit | 7 | 6 of 7 | 7 of 7 |
| Agent, no feedback | medusa-17032-counter | 7 | 6 of 7 | 7 of 7 |
| Agent, no feedback | medusa-16502-lines | 3 | 0 of 3 | 3 of 3 |
| Agent, with feedback | medusa-17032-last-unit | 5 | 4 of 5 | 5 of 5 |
| Agent, with feedback | medusa-17032-counter | 6 | 5 of 6 | 6 of 6 |
| Agent, with feedback | medusa-16502-lines | 2 | 1 of 2 | 2 of 2 |
| Agent, no cause list | medusa-17032-last-unit | 9 | 8 of 9 | not asked |
| Agent, no cause list | medusa-17032-counter | 9 | 8 of 9 | not asked |

A file match alone says little: naming the inventory module file every time would match the answer key for all three scenarios. The [benchmark page](benchmark/README.md#scoring) scores such fixed guesses.

## 5. What it means

- **Fastest on the last-unit race, when it finds it.** The agent's median was 33 runs, against 58.5 for the grid and 110 for random.
- **Tied by the grid on the counter race.** Both had a median of 33 runs. The grid found it in 10 of 10 trials, the agent in 7 of 10.
- **Less reliable than the grid.** The grid reproduced every scenario in every trial. The agent missed each race scenario in 3 of 10 trials.
- **Rarely finds all three scenarios, because it stops early.** It ended its trials after a median of 33 to 43 runs, while 300 were allowed, and seldom tried two cart lines that share stock.
- **Feedback made it worse.** Seeing its test results, it reproduced each scenario in fewer trials and never all three in one trial.
- **Hiding the cause list did not hurt** on the two race scenarios: 9 of 10 trials each, at the same median of 33. It never reproduced the two-lines scenario without the list.
- **What 10 trials can't tell us.** A gap of two or three trials out of 10, like 7 against 9, can easily come from chance. So none of these differences is called significant. The results also say nothing yet about other shops, other bugs or other AI models.

## 6. Guided trials, briefly (open-book)

In a guided trial the agent was handed the public bug report first, like an open-book test. These trials show whether it can turn a report into a working test. They are not a fair race against the simple methods, which got no report. Data: [prompt v1](benchmark/agent/guided-haiku-1/), [prompt v2](benchmark/agent/guided-haiku-2/).

| Bug report given | Prompt | Feedback | Trials | Reproduced the reported bug |
|---|---|---|---|---|
| #16502 | v1 | none | 3 | 3 of 3 |
| #16502 | v1 | history | 3 | 3 of 3 |
| #17032 | v1 | none | 3 | 0 of 3 |
| #17032 | v1 | history | 3 | 0 of 3 |
| #17032 | v2 | none | 3 | 0 of 3 |
| #17032 | v2 | history | 3 | 2 of 3 |

Given the #17032 report, the agent first tested with one server, while that bug needs two. Prompt v2 told it to match the conditions in the report, and with feedback it then reproduced the bug in 2 of 3 trials.

## 7. Safety

- **Local copies only.** Every run used a private copy of the shop on one computer, never a live shop or anyone's server.
- **The stop rule.** If any run breaks a rule that no public bug report covers, everything stops, the result stays on that computer, and nothing about it is published. A new bug would be reported privately to the Medusa team first.
- **Held results.** When a failure could not be pinned on one known bug, the trial was held and its test was run again many times before it was published.
- **The two stops in the 10-trial plan:**
  - One trial was stopped by our safety rule after a single run showed a failure outside the three cases that we could not repeat; its record is held for now, and the trial was rerun.
  - After the plan, an automatic re-check stopped it at random seed 10. That test had both bugs at once, and the re-check tried one fix at a time, so the failure stayed. With the #16502 fix and Redis locking applied together, the failure was gone in all 60 runs, for seed 10 and for seed 4, which had the same kind of test. Redis locking is Medusa's shared lock for several servers, which avoids the #17032 bug. Both trials are published with these extra runs.

## 8. Limits

- **Small samples.** 10 trials per method.
- **One shop engine.** Only Medusa, and only version 2.22.0.
- **Few bugs.** 3 scenarios from 2 root causes.
- **What the model may know.** The model may know general facts about this kind of bug. The two bug reports were opened on 2026-08-20 and 2026-09-27, after the model's training cutoff of June 2026.
- **An informed baseline.** The grid was designed knowing what these bugs look like.
- **The prompt was tuned once.** Prompt v2 was written after seeing the v1 results.
- **The agent sees the check names.** It knows which rules the checker tests, which hints at what to look for.
- **False alarms on fixed copies were not tested.** We never ran the agent on a shop with the bugs fixed, so we don't know how often it would claim a bug that is not there.

## 9. What went wrong along the way

- Given the #17032 report, the first prompt let the agent test with one server, while that bug needs two.
- In the first prompt, the agent with no feedback could see how many runs were left, which hinted whether a test had found something.
- The first prompt let the agent read Medusa's Enterprise Edition files, which have a different license.
- The first prompt trimmed old results every turn, which made the prompt cache work poorly and cost more.
- Early checks of the #17032 bugs compared two servers with one server, which does not show that a fix clears the bug.
- Five early baseline tests were labeled "cause not isolated" when they had really run out of budget before their fix checks.
- The automatic re-check tried one fix at a time, so it stopped the plan on a test that had both bugs.
- The plan's status count once showed 39 of 38 trials, because one trial was counted twice.
- A results page once described one trial's test wrongly, and another linked to the wrong folder.
- The baseline runner's log was buffered, so the plan log showed trial starts late.

## 10. How to check or rerun it

**Check the numbers.** This needs no Docker, no API key and no money:

```bash
make venv PYTHON=python3.14
```

```bash
make oversold
```

```bash
make test
```

`make test` runs every test, including the numbers check, which rebuilds every results table on this page and in the READMEs from the saved data. To recheck every saved run's verdict with Oversold, follow [How to recheck](benchmark/README.md#how-to-recheck).

**Rerun it.** This needs the local Docker engine described in the [README](README.md#how-to-run). A grid or random trial takes about 34 to 43 minutes and costs nothing. An agent trial needs an Anthropic API key in `.env`, takes about 4 minutes and has cost under 2 US cents each. The 30 unguided agent trials above cost $0.2173 in total. The plan that ran trials 4 to 10 is [benchmark/agent/plans/scale-10.yaml](benchmark/agent/plans/scale-10.yaml):

```bash
.venv/bin/python -m shortfall.trials benchmark/agent/plans/scale-10.yaml --raise-dollar-cap 3
```

**Where the raw data lives.** Every run is saved with its full history:

- [benchmark/cases/](benchmark/cases/): the three scenarios, their fixes and their measured runs.
- [benchmark/baselines/2004ed5/](benchmark/baselines/2004ed5/): every grid and random trial.
- [benchmark/agent/](benchmark/agent/): every agent trial, with its tests, claims, costs and the full conversation with the model.
