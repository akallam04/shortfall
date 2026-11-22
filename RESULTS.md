# Results

This page explains what Shortfall found, in plain words. Every table here is rebuilt from the saved data by a test, and the test fails if any number in it changes.

## 1. In one minute

[See one real trial, step by step](WALKTHROUGH.md): what the agent read, what it guessed, the test it wrote and what Oversold found.

- We asked whether a cheap AI agent that reads a shop's code can find real race-condition and inventory-consistency bugs in its checkout faster than two simple searches that use no AI, with the same budget of 300 test runs.
- The simple fixed-list search found all three known bug scenarios in every one of its 10 tries. The agent found all three in at most 3 of 10 tries.
- When the agent found the "last item sold twice" scenario, it found it fast: a median of 33 runs, against 58.5 for the fixed list. Once its misses count, this speed gap could be chance. On the other two-shoppers scenario, the fixed list tied it at 33.
- The agent stopped early, after a median of 33 to 43 of its 300 runs, so it rarely went on to look for the third scenario.
- With its test results shown, the agent did worse in these trials, but the gap could be chance. Hiding its list of likely causes did not hurt on the two two-shoppers scenarios, and no gap was clear either way.
- One agent try cost under 2 US cents and took about 4 minutes. Ten tries per method is still a small sample.
- **Follow-up experiments, with the tests chosen first.** Not allowed to stop early, the agent found all three scenarios in 7 of 10 tries. The bigger model Claude Sonnet 5.5 found all three in 9 of 10, at about 40 US cents a try. Both beat the earlier 3 of 10, but neither gap passed the test we set in advance, so either could still be chance.

## 2. The question

Can a cheap AI agent that reads the code find real race-condition and inventory-consistency bugs in a shop's checkout faster than simple searches, with the same run budget and a checker it can't change?

A race condition is a bug that only shows up when two or more shoppers act at the same moment. An inventory-consistency bug is one where the shop sells stock it does not have, or its count of reserved stock stops matching its reservations. The two #17032 scenarios are race conditions that break inventory consistency. The two-lines scenario (#16502) breaks it with no concurrency at all: a single checkout of one cart is enough.

## 3. How the test works

**The shop software.** We tested Medusa 2.22.0, an open-source online shop engine. Every test ran on a fresh private copy of the shop on one computer, never on a real shop.

**The three known bug scenarios.** The benchmark uses three test scenarios built from two bugs that were already public:

- **Last unit sold twice** ([#17032](https://github.com/medusajs/medusa/issues/17032)): two shoppers buy the last item through two servers at once, and both purchases go through.
- **Reserved count goes wrong** ([#17032](https://github.com/medusajs/medusa/issues/17032)): the shop's count of stock set aside for orders loses updates when two servers work at once.
- **Two cart lines oversold** ([#16502](https://github.com/medusajs/medusa/issues/16502)): one cart has two lines that use the same stock, and the shop checks each line alone.

A scenario is a small test file: which items are in stock, which shoppers there are, and when they press Buy. In the tables below the three scenarios are called `medusa-17032-last-unit`, `medusa-17032-counter` and `medusa-16502-lines`.

**What "reproduced" means.** A run is one go of a test on a fresh copy of the shop. A scenario counts as reproduced when a test breaks the shop's rule on plain Medusa, and the same test passes on a copy of Medusa with the public fix for that bug: pull request [#17420](https://github.com/medusajs/medusa/pull/17420) for #17032 and pull request [#16961](https://github.com/medusajs/medusa/pull/16961) for #16502.

**Two more terms.** A claim is **backed by a violation** when a check failed on plain Medusa in the attempt it names. A claim not backed by a violation is a false alarm. A test **named the right place** when the source file and the cause the agent gave with it, before its runs, both match the answer key for the scenario it reproduced.

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

At the end of a trial the agent lists its claims: the tests it believes found a real problem. A claim is **backed by a violation** when that test broke a rule on plain Medusa, and **not backed by a violation** when it did not. A claim not backed by a violation is a false alarm. Data: [agent trials 1 to 3](benchmark/agent/unguided-haiku-1/), [agent trials 4 to 10](benchmark/agent/scale-10/).

| Method | Trials | Trials that called finish | Claims backed by a violation | Claims not backed by a violation |
|---|---|---|---|---|
| Agent, no feedback | 10 | 10 | 2 | 0 |
| Agent, with feedback | 10 | 10 | 9 | 0 |
| Agent, no cause list | 10 | 7 | 2 | 1 |

"Called finish" means the agent ended the trial itself and listed its claims. In three trials without the cause list, the model stopped replying with a tool call before it did that.

### Did it name the right place?

With every test the agent names the source file it suspects and, except without the cause list, one cause from a fixed list. Both are saved before the test runs. For each trial that reproduced a scenario, this table counts how often that file and that cause matched the answer key, and how often both did, which is what named the right place means. Data: the agent folders above and the [answer keys](benchmark/cases/).

| Method | Test scenario | Trials that reproduced it | File matched | Cause matched | Named the right place |
|---|---|---|---|---|---|
| Agent, no feedback | medusa-17032-last-unit | 7 | 6 of 7 | 7 of 7 | 6 of 7 |
| Agent, no feedback | medusa-17032-counter | 7 | 6 of 7 | 7 of 7 | 6 of 7 |
| Agent, no feedback | medusa-16502-lines | 3 | 0 of 3 | 3 of 3 | 0 of 3 |
| Agent, with feedback | medusa-17032-last-unit | 5 | 4 of 5 | 5 of 5 | 4 of 5 |
| Agent, with feedback | medusa-17032-counter | 6 | 5 of 6 | 6 of 6 | 5 of 6 |
| Agent, with feedback | medusa-16502-lines | 2 | 1 of 2 | 2 of 2 | 1 of 2 |
| Agent, no cause list | medusa-17032-last-unit | 9 | 8 of 9 | not asked | not asked |
| Agent, no cause list | medusa-17032-counter | 9 | 8 of 9 | not asked | not asked |

The file and the cause in the agent's final claims are recorded as its diagnosis after results: they are given after the tests ran, and in the history mode after the agent saw how they did. They are graded on their own, in each trial's `claims.json`, and never replace what was saved before the runs. This table does not use them. In 2 of the 43 claims in all published trials, the diagnosis differs from the attempt's saved file and cause.

Fixed guesses that use no AI, scored from the answer keys on the three scenarios, show what each column is worth on its own:

| Fixed guess, no AI | File matched | Cause matched | Named the right place |
|---|---|---|---|
| Always `inventory-module.ts`, no cause | 3 of 3 | 0 of 3 | 0 of 3 |
| Always the most common cause, `process-local-lock`, no file | 0 of 3 | 2 of 3 | 0 of 3 |
| Always `inventory-module.ts` and `process-local-lock` | 3 of 3 | 2 of 3 | 2 of 3 |

Naming the inventory module file every time matches the file for all three scenarios, and naming the most common cause every time matches 2 of 3. So a file match alone says little, and the agent's cause and named-the-right-place counts should be read next to these.

### Negative controls

A fix build, or Redis locking for #17032, should clear the failure that its bug causes. This table counts every committed run on a fix build or with Redis locking, of a test whose failure on plain Medusa is credited to the bug that the build fixes, and how many of those runs still broke that rule. Data: the [case results](benchmark/cases/), every published trial's ledger and every `review/` folder.

| Fix build or Redis run | Runs | Runs where the covered rule failed |
|---|---|---|
| The three reference scenarios on their fix build | 90 | 0 |
| The two #17032 reference scenarios with Redis locking | 240 | 0 |
| Fix-build controls of tests credited as reproduced | 2980 | 0 |
| Review runs with the fix or locking the review found covers the failure | 1020 | 0 |
| All of the above | 4330 | 0 |
| For contrast: fix-build controls of tests not credited to that fix | 1860 | 1572 |

For the controls of tests credited as reproduced, 0 is partly by design, because a test is credited only when its fix control passes. The other rows are checks made apart from that. In the last row the fix control failed in most runs, because those tests broke the rule through the other bug, and that is how the scoring tells the two bugs apart. Across all 53 unguided agent trials, the agent made 26 claims, and 2 of them were not backed by a violation. The agent was never run against patched code, so we don't know how often it would claim a bug in a shop where the bugs are fixed.

## 5. What it means

- **Fastest on the last-unit race, when it finds it.** The agent's median was 33 runs, against 58.5 for the grid and 110 for random. Once its misses count, this speed gap could be chance.
- **Tied by the grid on the counter race.** Both had a median of 33 runs. The grid found it in 10 of 10 trials, the agent in 7 of 10.
- **Less reliable than the grid.** The grid reproduced every scenario in every trial. The agent missed each race scenario in 3 of 10 trials.
- **Rarely finds all three scenarios, because it stops early.** It ended its trials after a median of 33 to 43 runs, while 300 were allowed, and seldom tried two cart lines that share stock.
- **With feedback it did worse in these trials, but the gap could be chance.** Seeing its test results, it reproduced each scenario in fewer trials and never all three in one trial.
- **Hiding the cause list did not hurt** on the two race scenarios: 9 of 10 trials each, at the same median of 33. It never reproduced the two-lines scenario without the list. No gap between the two versions was clear either way.
- **The grid found all three scenarios far more often than any agent version** (10 of 10, against 0 to 3 of 10), and the same holds for the two-lines scenario. These gaps pass a standard statistics test. For the agent with no feedback they pass when its own 8 tests are corrected together, and narrowly miss when all 24 tests are.
- **The other gaps are small enough that chance could explain them**, including the agent's speed on the race scenarios once its misses count.
- **We chose these tests after seeing the data**, so treat them as a guide. The results also say nothing yet about other shops, other bugs or other AI models.

### Statistics, run after the fact

A p-value is the chance of seeing a gap at least this large if the two methods were really equally good. A value under 0.05 is the usual bar for "unlikely to be chance".

Running many tests at once makes some small p-values appear by luck, so Holm's correction raises each p-value to allow for that. It is applied twice: across all 24 tests below, and across the 8 tests of the agent with no feedback alone. The tests are Fisher's exact test, two-sided, on how many of 10 trials found each scenario. Data: the same folders as the first table in section 4.

| Agent version | Compared with | Scenario | Agent found it | Other method found it | p-value | After Holm, all 24 | After Holm, the no-feedback agent's 8 |
|---|---|---|---|---|---|---|---|
| No feedback | Grid | medusa-17032-last-unit | 7 of 10 | 10 of 10 | 0.21 | 1 | 1 |
| No feedback | Grid | medusa-17032-counter | 7 of 10 | 10 of 10 | 0.21 | 1 | 1 |
| No feedback | Grid | medusa-16502-lines | 3 of 10 | 10 of 10 | 0.0031 | 0.062 | 0.025, passes |
| No feedback | Grid | All three in one trial | 3 of 10 | 10 of 10 | 0.0031 | 0.062 | 0.025, passes |
| No feedback | Random | medusa-17032-last-unit | 7 of 10 | 9 of 10 | 0.58 | 1 | 1 |
| No feedback | Random | medusa-17032-counter | 7 of 10 | 10 of 10 | 0.21 | 1 | 1 |
| No feedback | Random | medusa-16502-lines | 3 of 10 | 7 of 10 | 0.18 | 1 | 1 |
| No feedback | Random | All three in one trial | 3 of 10 | 6 of 10 | 0.37 | 1 | 1 |
| With feedback | Grid | medusa-17032-last-unit | 5 of 10 | 10 of 10 | 0.033 | 0.49 | not in this group |
| With feedback | Grid | medusa-17032-counter | 6 of 10 | 10 of 10 | 0.087 | 1 | not in this group |
| With feedback | Grid | medusa-16502-lines | 2 of 10 | 10 of 10 | 0.00071 | 0.015, passes | not in this group |
| With feedback | Grid | All three in one trial | 0 of 10 | 10 of 10 | under 0.0001 | 0.00026, passes | not in this group |
| With feedback | Random | medusa-17032-last-unit | 5 of 10 | 9 of 10 | 0.14 | 1 | not in this group |
| With feedback | Random | medusa-17032-counter | 6 of 10 | 10 of 10 | 0.087 | 1 | not in this group |
| With feedback | Random | medusa-16502-lines | 2 of 10 | 7 of 10 | 0.07 | 0.98 | not in this group |
| With feedback | Random | All three in one trial | 0 of 10 | 6 of 10 | 0.011 | 0.18 | not in this group |
| No cause list | Grid | medusa-17032-last-unit | 9 of 10 | 10 of 10 | 1 | 1 | not in this group |
| No cause list | Grid | medusa-17032-counter | 9 of 10 | 10 of 10 | 1 | 1 | not in this group |
| No cause list | Grid | medusa-16502-lines | 0 of 10 | 10 of 10 | under 0.0001 | 0.00026, passes | not in this group |
| No cause list | Grid | All three in one trial | 0 of 10 | 10 of 10 | under 0.0001 | 0.00026, passes | not in this group |
| No cause list | Random | medusa-17032-last-unit | 9 of 10 | 9 of 10 | 1 | 1 | not in this group |
| No cause list | Random | medusa-17032-counter | 9 of 10 | 10 of 10 | 1 | 1 | not in this group |
| No cause list | Random | medusa-16502-lines | 0 of 10 | 7 of 10 | 0.0031 | 0.062 | not in this group |
| No cause list | Random | All three in one trial | 0 of 10 | 6 of 10 | 0.011 | 0.18 | not in this group |

Speed: a two-sided Mann-Whitney test on runs to first reproduction, for the agent with no feedback, with a miss counted as over 300 runs.

| Scenario | Compared with | Agent median runs | Other method median runs | p-value |
|---|---|---|---|---|
| medusa-17032-last-unit | Grid | 33 | 58.5 | 0.84 |
| medusa-17032-counter | Grid | 33 | 33 | 0.48 |
| medusa-17032-last-unit | Random | 33 | 110 | 0.11 |
| medusa-17032-counter | Random | 33 | 46.5 | 0.61 |

Agent against agent, also chosen after seeing the data: Fisher's exact test, two-sided, for the agent with no feedback against the other two agent versions.

| No-feedback agent against | Scenario | No-feedback agent found it | Other version found it | p-value |
|---|---|---|---|---|
| With feedback | medusa-17032-last-unit | 7 of 10 | 5 of 10 | 0.65 |
| With feedback | medusa-17032-counter | 7 of 10 | 6 of 10 | 1 |
| With feedback | medusa-16502-lines | 3 of 10 | 2 of 10 | 1 |
| With feedback | All three in one trial | 3 of 10 | 0 of 10 | 0.21 |
| No cause list | medusa-17032-last-unit | 7 of 10 | 9 of 10 | 0.58 |
| No cause list | medusa-17032-counter | 7 of 10 | 9 of 10 | 0.58 |
| No cause list | medusa-16502-lines | 3 of 10 | 0 of 10 | 0.21 |
| No cause list | All three in one trial | 3 of 10 | 0 of 10 | 0.21 |

## 6. Follow-up experiments: the whole budget and a bigger model

The first results raised two questions, and we ran one experiment for each. This time the tests were chosen before any trial ran: they were written into the [plan file](benchmark/agent/plans/followups-1.yaml) and pushed first. Data: [benchmark/agent/followups-1](benchmark/agent/followups-1/).

- **Did the agent miss scenarios only because it stopped early?** Claude Haiku 5.5 ran the same task as before, on the same prompt except for one line, but it could not end a trial while more than 60 of its 300 runs were left. When it tried, it got one fixed line telling it to keep testing. We call that line a gate answer.
- **Does a bigger model stop early less often, or find more?** Claude Sonnet 5.5 ran the same task on the same prompt as the Haiku agent with no feedback, with nothing changed.

Both arms ran 10 unguided trials with no feedback, each with at most 300 runs, 30 attempts, 100 turns and $1. Each arm is compared with Haiku 5.5 on prompt v2 with no feedback, the "Agent, no feedback" column in section 4, and with the grid.

**The first whole-budget arm was replaced after 3 trials.** In its first version, every gate answer used up one of the 100 turns. In 2 of its 3 trials the agent kept replying without a new test, waiting for run results that this mode never shows, and reached the 100-turn cap after 119 and 129 runs. So that arm could not tell whether stopping early was the problem. We closed it and replaced it before a 4th trial. In the new version the gate answer says that run results never come in this mode, gate answers do not use up turns, and a trial ends after 15 gate answers. The new arm has the same tests as the old one, pushed before its first trial. The 3 closed trials are published and shown below, without tests.

### What the follow-up arms found

Each cell says in how many trials the scenario was reproduced, and the median runs to its first reproduction, counted as in section 4. The closed arm's cells are out of its 3 trials.

| Test scenario | Haiku 5.5 on v2 | Haiku 5.5, whole budget | Sonnet 5.5 | Grid | Haiku 5.5, first gate, closed |
|---|---|---|---|---|---|
| medusa-17032-last-unit | 7 of 10, median 33 | 10 of 10, median 38 | 9 of 10, median 71 | 10 of 10, median 58.5 | 3 of 3, median 33 |
| medusa-17032-counter | 7 of 10, median 33 | 10 of 10, median 33 | 9 of 10, median 71 | 10 of 10, median 33 | 3 of 3, median 33 |
| medusa-16502-lines | 3 of 10, median over 300 | 7 of 10, median 178.5 | 9 of 10, median 23 | 10 of 10, median 54 | 1 of 3, median over 300 |
| All three in one trial | 3 of 10 | 7 of 10 | 9 of 10 | 10 of 10 | 1 of 3 |

### Cost and time per trial

"Called finish" means the agent ended the trial itself and listed its claims. A gate answer is the fixed line sent when the agent tried to stop with more than 60 runs left.

| Arm | Trials | Median runs used | Median turns | Median attempts | Called finish | Claims backed by a violation | Claims not backed by a violation | Median dollars | Total dollars | Median minutes | Median gate answers |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Haiku 5.5, whole budget | 10 | 238 | 44.5 | 12 | 1 | 3 | 0 | 0.0388 | 0.3796 | 23.4 | 14 |
| Sonnet 5.5 | 10 | 119 | 22.5 | 5 | 10 | 8 | 1 | 0.3937 | 4.3275 | 16 | none |
| Haiku 5.5, first gate, closed | 3 | 129 | 100 | 7 | 0 | 0 | 0 | 0.0579 | 0.1736 | 16.4 | 72 |

### The tests, chosen before the trials

Fisher's exact test, two-sided, on how many of 10 trials reproduced each scenario. Each arm has one primary test, which answers its question: trials that reproduced all three scenarios, against Haiku 5.5 on v2. Its 7 secondary tests are read only as a guide. Holm's correction is applied over each arm's 8 tests, and a test passes when its corrected p-value is under 0.05.

| Arm | Test | Compared with | Scenario | Arm found it | Other method found it | p-value | After Holm, the arm's 8 |
|---|---|---|---|---|---|---|---|
| Haiku 5.5, whole budget | primary | Haiku 5.5 on v2 | All three in one trial | 7 of 10 | 3 of 10 | 0.18 | 1 |
| Haiku 5.5, whole budget | secondary | Haiku 5.5 on v2 | medusa-17032-last-unit | 10 of 10 | 7 of 10 | 0.21 | 1 |
| Haiku 5.5, whole budget | secondary | Haiku 5.5 on v2 | medusa-17032-counter | 10 of 10 | 7 of 10 | 0.21 | 1 |
| Haiku 5.5, whole budget | secondary | Haiku 5.5 on v2 | medusa-16502-lines | 7 of 10 | 3 of 10 | 0.18 | 1 |
| Haiku 5.5, whole budget | secondary | Grid | medusa-17032-last-unit | 10 of 10 | 10 of 10 | 1 | 1 |
| Haiku 5.5, whole budget | secondary | Grid | medusa-17032-counter | 10 of 10 | 10 of 10 | 1 | 1 |
| Haiku 5.5, whole budget | secondary | Grid | medusa-16502-lines | 7 of 10 | 10 of 10 | 0.21 | 1 |
| Haiku 5.5, whole budget | secondary | Grid | All three in one trial | 7 of 10 | 10 of 10 | 0.21 | 1 |
| Sonnet 5.5 | primary | Haiku 5.5 on v2 | All three in one trial | 9 of 10 | 3 of 10 | 0.02 | 0.16 |
| Sonnet 5.5 | secondary | Haiku 5.5 on v2 | medusa-17032-last-unit | 9 of 10 | 7 of 10 | 0.58 | 1 |
| Sonnet 5.5 | secondary | Haiku 5.5 on v2 | medusa-17032-counter | 9 of 10 | 7 of 10 | 0.58 | 1 |
| Sonnet 5.5 | secondary | Haiku 5.5 on v2 | medusa-16502-lines | 9 of 10 | 3 of 10 | 0.02 | 0.16 |
| Sonnet 5.5 | secondary | Grid | medusa-17032-last-unit | 9 of 10 | 10 of 10 | 1 | 1 |
| Sonnet 5.5 | secondary | Grid | medusa-17032-counter | 9 of 10 | 10 of 10 | 1 | 1 |
| Sonnet 5.5 | secondary | Grid | medusa-16502-lines | 9 of 10 | 10 of 10 | 1 | 1 |
| Sonnet 5.5 | secondary | Grid | All three in one trial | 9 of 10 | 10 of 10 | 1 | 1 |

### What it means

- **Not allowed to stop early, Haiku found all three scenarios in 7 of 10 trials,** against 3 of 10 when it could stop early. It used a median of 238 runs instead of 43, reproduced both race scenarios in all 10 trials instead of 7, and the two-lines scenario in 7 instead of 3. Its primary test did not pass, so this gap could be chance.
- **Sonnet 5.5 found all three in 9 of 10 trials,** against 3 of 10 for Haiku. Its primary test had a p-value of 0.02 before the correction and 0.16 after it, so by the bar we set in advance this gap could also be chance.
- **Sonnet still stopped early, but tried two cart lines early.** It called finish in every trial, after a median of 119 runs. It usually reproduced the two-lines scenario first, at a median of 23 runs, and the two race scenarios later, at a median of 71.
- **Sonnet cost about ten times as much.** A median of $0.39 per trial, against $0.04 for Haiku not allowed to stop early.
- **The one Sonnet trial that found nothing never ran a test.** In all 7 of its submissions it put the scenario inside the text of its hypothesis instead of in its own field, so each was refused. It then called finish. It counts as a miss.
- **Haiku seldom ended a trial itself when it had to use the budget.** It called finish in 1 of 10 trials. 5 trials ended after 15 gate answers, and in 4 it stopped replying with a tool call once 60 or fewer runs were left.
- **The grid still reproduced all three scenarios in 10 of 10 trials.** No test against the grid passed for either arm.

### Held trials, reviewed by hand

Three trials of this plan were held after it ended: sonnet-none-3, sonnet-none-5 and budget2-none-6. In each, one cart became two orders in a run with two servers and the default in-memory lock, the failure described in [One cart, two orders](#one-cart-two-orders). The plan file sets out how such a trial is reviewed. That rule was added during the plan, after two of these trials were held and before any of them was reviewed: each held test is run 100 times as is, 100 times with Redis locking, 100 times with all completions sent to server 1, and 100 times with the #17032 fix for information only. If one cart never becomes two orders with Redis locking or on server 1, the trial is labeled "documented limit of in-memory locking" and published with its review runs.

| Held trial | Test | Runs | Runs where one cart became two orders |
|---|---|---|---|
| sonnet-none-3, attempt 3 | The trial's own runs | 13 | 1 |
| sonnet-none-3, attempt 3 | Run again as is | 100 | 7 |
| sonnet-none-3, attempt 3 | Redis locking | 100 | 0 |
| sonnet-none-3, attempt 3 | All completions sent to server 1 | 100 | 0 |
| sonnet-none-3, attempt 3 | With the #17032 fix, pull request #17420 | 100 | 9 |
| sonnet-none-5, attempt 3 | The trial's own runs | 13 | 1 |
| sonnet-none-5, attempt 3 | Run again as is | 100 | 2 |
| sonnet-none-5, attempt 3 | Redis locking | 100 | 0 |
| sonnet-none-5, attempt 3 | All completions sent to server 1 | 100 | 0 |
| sonnet-none-5, attempt 3 | With the #17032 fix, pull request #17420 | 100 | 4 |
| budget2-none-6, attempt 4 | The trial's own runs | 13 | 1 |
| budget2-none-6, attempt 4 | Run again as is | 100 | 1 |
| budget2-none-6, attempt 4 | Redis locking | 100 | 0 |
| budget2-none-6, attempt 4 | All completions sent to server 1 | 100 | 0 |
| budget2-none-6, attempt 4 | With the #17032 fix, pull request #17420 | 100 | 0 |
| budget2-none-6, attempt 7 | The trial's own runs | 13 | 2 |
| budget2-none-6, attempt 7 | Run again as is | 100 | 4 |
| budget2-none-6, attempt 7 | Redis locking | 100 | 0 |
| budget2-none-6, attempt 7 | All completions sent to server 1 | 100 | 0 |
| budget2-none-6, attempt 7 | With the #17032 fix, pull request #17420 | 100 | 2 |
| budget2-none-6, attempt 12 | The trial's own runs | 20 | 1 |
| budget2-none-6, attempt 12 | Run again as is | 100 | 6 |
| budget2-none-6, attempt 12 | Redis locking | 100 | 0 |
| budget2-none-6, attempt 12 | All completions sent to server 1 | 100 | 0 |
| budget2-none-6, attempt 12 | With the #17032 fix, pull request #17420 | 100 | 2 |

No check failed with Redis locking or with all completions sent to server 1, in any of the five held tests. One cart became two orders only with two servers and the in-memory lock: in 1 to 7 of 100 runs as is, and in 0 to 9 of 100 with the #17032 fix, a set run for information only. The reserved-count check also failed in 28 to 83 of 100 runs as is. That is the #17032 counter scenario, which these trials had already reproduced, and it never failed with Redis locking, on server 1 or with the fix. As before, a checkout that lost the race was refused with an HTTP 400 error, almost always "Cannot create multiple links between 'order' and 'payment'", and with Redis locking or on server 1 no checkout was refused.

So all three trials are labeled "documented limit of in-memory locking", published with their review runs in their `review/` folders, and counted. The review runs do not change any trial's score.

## 7. Guided trials, briefly (open-book)

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

## 8. Safety

- **Local copies only.** Every run used a private copy of the shop on one computer, never a live shop or anyone's server.
- **The stop rule.** If any run breaks a rule that no public bug report covers, everything stops, the result stays on that computer, and nothing about it is published. A new bug would be reported privately to the Medusa team first.
- **Held results.** When a failure could not be pinned on one known bug, the trial was held and its test was run again many times before it was published.
- **The stop at random seed 10.** After the plan, an automatic re-check stopped it at random seed 10. That test had both bugs at once, and the re-check tried one fix at a time, so the failure stayed. With the #16502 fix and Redis locking applied together, the failure was gone in all 60 runs, for seed 10 and for seed 4, which had the same kind of test. Redis locking is Medusa's shared lock for several servers, which avoids the #17032 bug. Both trials are published with these extra runs.
- **Two trials stopped by the safety rule.** In both, one cart became two orders in a single run. Both trials were rerun from scratch, and the reruns are the ones counted. The next part explains what the extra runs showed.
- **Three trials held for the same failure.** After that failure was added to the list of covered failures, three trials of the follow-up plan were held for it instead of stopped, and reviewed by hand with 100 runs per test. The results are in [section 6](#held-trials-reviewed-by-hand).

### One cart, two orders

Two agent trials were stopped by the safety rule: nomenu-none-8 in the 10-trial plan and sonnet-none-3 in the follow-up plan. In both, the agent wrote a test that sends the same cart to checkout at the same moment through both servers. In one run of each, one cart became two orders. That breaks the rule that one cart becomes at most one order, and none of the three scenarios covers it. We then ran both tests again many times on plain Medusa 2.22.0:

| Stopped trial | Test | Runs | Runs where one cart became two orders |
|---|---|---|---|
| nomenu-none-8, 10-trial plan | The trial's own runs | 10 | 1 |
| nomenu-none-8, 10-trial plan | Run again as is | 60 | 0 |
| nomenu-none-8, 10-trial plan | Redis locking | 60 | 0 |
| nomenu-none-8, 10-trial plan | Both completions on one server | 60 | 0 |
| nomenu-none-8, 10-trial plan | Stock raised from 1 to 5 | 60 | 0 |
| nomenu-none-8, 10-trial plan | Run again as is | 600 | 0 |
| sonnet-none-3, follow-up plan | The trial's own runs | 13 | 1 |
| sonnet-none-3, follow-up plan | Run again as is | 100 | 4 |
| sonnet-none-3, follow-up plan | Redis locking | 100 | 0 |
| sonnet-none-3, follow-up plan | All completions sent to server 1 | 100 | 0 |
| sonnet-none-3, follow-up plan | With the #17032 fix, pull request #17420 | 100 | 8 |

- One cart became two orders only with two servers and Medusa's default in-memory lock. It never happened with Redis locking, or when every checkout went to one server.
- It was rare in the first test, which has one cart: 1 of its 10 trial runs, then 0 of 660 more runs as is. The second test completes five carts at once, and it happened in 4 of 100 runs.
- The fix for #17032 did not stop it: one cart still became two orders in 8 of 100 runs. That fix targets the stock reservation bug, not the lock on a cart, and this set is shown for information only.
- In the runs as is, the checkout that lost the race was usually refused with an HTTP 400 error, "Cannot create multiple links between 'order' and 'payment'". With Redis locking, or with one server, no checkout was refused, and both checkouts of a cart returned the same order.

Pooled over every review of this failure, the two stopped trials above and the three held trials in [section 6](#held-trials-reviewed-by-hand):

| Setting, pooled over every review | Runs | Runs where one cart became two orders | Upper bound at 95% confidence |
|---|---|---|---|
| Two servers, in-memory lock, run again as is | 1260 | 24 | does not apply |
| Redis locking | 660 | 0 | 0.45% |
| Every checkout on one server | 660 | 0 | 0.45% |

With two servers and the in-memory lock it happened in 24 of 1,260 runs. 0 of 660 runs with Redis locking and 0 of 660 with every checkout on one server means the rate in those settings is at most about 0.5%, at 95% confidence.

Medusa's in-memory lock only works inside one server. Medusa's knowledge base says the in-memory locking provider is meant for development only. The sources are Medusa's [Redis locking docs](https://docs.medusajs.com/resources/infrastructure-modules/locking/redis), the [knowledge base page](https://medusajs.com/kb/tickets-and-bookings/bookings-and-reservations), Medusa's docs on [storing workflow executions](https://docs.medusajs.com/learn/fundamentals/workflows/store-executions), and an [AppCrates article](https://appcrates.pl/en/blog/medusa-js-na-produkcji-architektura-sklepu) on running Medusa in production, which names the same risk: "One payment, two servers, potentially two orders." These results are consistent with that documented limit, so we count this failure as a documented limit of in-memory locking, not as a new bug. Shortfall's list of covered failures now includes it for two servers with in-memory locking. Both stopped records are published with these extra runs in [benchmark/agent/stopped](benchmark/agent/stopped/).

## 9. Limits

- **Small samples.** 10 trials per method, and 3 for the closed whole-budget arm.
- **One shop engine.** Only Medusa, and only version 2.22.0.
- **Few bugs.** 3 scenarios from 2 root causes.
- **What the models may know.** The models may know general facts about this kind of bug. The two bug reports were opened on 2026-08-20 and 2026-09-27, after the training cutoff of both models, June 2026.
- **Two models, run a little differently.** Claude Sonnet 5.5 cannot turn its extended thinking off, so it ran at its lowest thinking setting. Claude Haiku 5.5 ran without it.
- **The follow-up arms ran later.** They ran in a later session than the Haiku arm they are compared with, on the same images, Oversold commit, scoring and prompt v2.
- **An informed baseline.** The grid was designed knowing what these bugs look like.
- **The prompt was tuned once.** Prompt v2 was written after seeing the v1 results.
- **The agent sees the check names.** It knows which rules the checker tests, which hints at what to look for.
- **Tests chosen after the fact, then ahead.** The statistics tests in section 5 were chosen after seeing the data. The tests of the follow-up experiments in section 6 were chosen before their trials ran.
- **The whole-budget arm forces, it does not ask.** It tests what happens when the agent cannot stop early, not a prompt that asks it to keep going.
- **One Oversold check can say pass when it should not.** In Oversold v0.1.1, `no_missing_orders` skips a cart when any checkout of that cart has an unknown outcome, and can still say pass. Oversold now documents this in its [known limits](https://github.com/akallam04/oversold/commit/25643fe96a10219a9d4a7c74907cc80079158215), and Shortfall stays pinned to v0.1.1. Shortfall counts every run with such a checkout as inconclusive for every check, never as a pass. 39 of Shortfall's 16,994 committed runs had a checkout with an unknown outcome, and all 39 are marked inconclusive. In every one of them Oversold said pass on all five checks.
- **False alarms on fixed copies were not tested.** We never ran the agent on a shop with the bugs fixed, so we don't know how often it would claim a bug that is not there.

## 10. What went wrong along the way

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
- The first whole-budget arm counted every gate answer as a turn, so in 2 of its 3 trials the agent used up its 100 turns while it waited for run results. It was closed after 3 trials and replaced.
- In one Sonnet trial, sonnet-none-4, the model put its scenario inside the text of its hypothesis in all 7 submissions, so each was refused for having no scenario and the trial ran no tests. It counts as a miss.
- The follow-up plan was interrupted once, when the terminal session that started it closed and took the engine with it. The trial that was running, sonnet-none-4, was rerun from scratch. After the engine restarted, Oversold's database was not running, and the next try of that trial stopped with a misleading error about image inputs. It was rerun from scratch again. Plans now start through a launcher that brings the database up first, and every trial first checks that the database answers.
- The plan put each arm's primary test in the same correction as its seven secondary tests, which raised the bar for the primary test from 0.05 to 0.00625. Tested alone, Sonnet's primary test (p = 0.02) would have passed. We report the result as planned.

## 11. How to check or rerun it

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

**Rerun it.** This needs the local Docker engine described in the [README](README.md#how-to-run). A grid or random trial takes about 34 to 43 minutes and costs nothing. An agent trial needs an Anthropic API key in `.env`. A Haiku trial on prompt v2 takes about 4 minutes and has cost under 2 US cents each. The 30 unguided agent trials in section 4 cost $0.2173 in total. The plan that ran trials 4 to 10 is [benchmark/agent/plans/scale-10.yaml](benchmark/agent/plans/scale-10.yaml):

```bash
.venv/bin/python -m shortfall.trials benchmark/agent/plans/scale-10.yaml --raise-dollar-cap 3
```

The follow-up experiments in section 6 are [benchmark/agent/plans/followups-1.yaml](benchmark/agent/plans/followups-1.yaml). Its 23 published trials cost $4.8807. The launcher runs it in the background:

```bash
.venv/bin/python -m shortfall.launch benchmark/agent/plans/followups-1.yaml --raise-dollar-cap 8
```

**Where the raw data lives.** Every run is saved with its full history:

- [benchmark/cases/](benchmark/cases/): the three scenarios, their fixes and their measured runs.
- [benchmark/baselines/2004ed5/](benchmark/baselines/2004ed5/): every grid and random trial.
- [benchmark/agent/](benchmark/agent/): every agent trial, with its tests, claims, costs and the full conversation with the model.
