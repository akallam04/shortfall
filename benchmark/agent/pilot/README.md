# Pilot trial

This folder holds one development run of the agent. It is not counted in any result.

It ran before the prompt fixes and before the prompts were frozen in [prompts.sha256](../prompts.sha256), so what the model saw differs from the frozen setup. In particular, its scenario format text still listed the `checks` field. Its first attempt set that field and was refused, which cost it attempt 1. At that time `submit_attempt` had no expected check and `finish` took no claims, so this trial has neither.

- Model: `claude-haiku-5-5`.
- Mode: guided, with the bug report of Medusa issue [#16502](https://github.com/medusajs/medusa/issues/16502). Feedback mode: history.
- Caps: 120 runs, 6 attempts, 40 turns and $0.50.
- It finished on its own after 6 turns, 2 attempts (1 refused) and 33 runs, for $0.0044.
- Its second attempt reproduced medusa-16502-lines: `no_oversell` failed in 13 of 13 runs on plain Medusa 2.22.0 and in 0 of 10 runs with the fix from pull request [#16961](https://github.com/medusajs/medusa/pull/16961). The file and cause it named match the answer key.

The trial is in [16502-history-1/](16502-history-1/):

- `score.json`: the trial's summary.
- `attempts.json` and `attempts/`: each attempt as submitted and as run, with its prediction and results.
- `claims.json`: empty, since finish took no claims then.
- `ledger.jsonl`: the trial's ledger lines.
- `transcript.jsonl.gz`: everything the model was shown and wrote, with anything that looks like a key masked. It quotes Medusa source code from files under the [MIT license](https://github.com/medusajs/medusa/blob/v2.22.0/LICENSE), and none from Medusa's Enterprise Edition files, which are under a different license.
- `runs/`: every Oversold run with its full history, rechecked by `oversold check --verify` in CI.

## Sonnet pilot

[sonnet-unguided-none-1/](sonnet-unguided-none-1/) is one development run of `claude-sonnet-5-5` on prompt version v2, made before plan [followups-1](../plans/followups-1.yaml). It is not counted. It checked that the API accepts this model's conversation after old tool results are shortened. This model thinks between tool calls, and its thinking is sent back unchanged.

- Mode: unguided. Feedback mode: none.
- Caps: 40 runs, 30 attempts, 100 turns and $0.40.
- It ran 13 turns and 2 attempts, and ended at its 40-run cap after 36 runs, for $0.2184.
- Old tool results were shortened before its 13th call, and the API accepted that call.
- Its first attempt reproduced medusa-16502-lines at run 23. The file and cause it named match the answer key.
- It made no claims, since it reached the run cap before it called finish.

The folder has the same layout as the one above.
