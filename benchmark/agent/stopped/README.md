# Stopped trials

Two agent trials were stopped by the safety rule, which stops a plan when a run breaks a rule that nothing in the coverage map covers. In both, the agent sent the same cart to checkout at the same moment through both servers, and in one run one cart became two orders. Each trial was rerun from scratch, and the rerun is the trial that counts. These folders keep the stopped records as they were, with the extra runs made afterwards.

- [scale-10-nomenu-none-8](scale-10-nomenu-none-8/): trial nomenu-none-8 of plan scale-10, one cart. Its rerun is in [scale-10/nomenu-none-8](../scale-10/nomenu-none-8/).
- [followups-1-sonnet-none-3](followups-1-sonnet-none-3/): trial sonnet-none-3 of plan followups-1, five carts. Its rerun is published with plan followups-1.

Each folder has the same layout as a published trial: `ledger.jsonl`, `transcript.jsonl.gz`, `attempts/`, `attempts.json`, `claims.json`, `score.json` and the trial's own runs under `runs/`. The extra runs are under `review/`, with `review/review.json` giving each set's runs, the failures of every check, and the HTTP errors returned to checkouts that failed. The scenario of each set is in its run folder.

The extra runs showed the failure only with two servers and Medusa's default in-memory lock, never with Redis locking or with every checkout on one server. Medusa's knowledge base says the in-memory locking provider is meant for development only. The failure is now in the coverage map as a documented limit of in-memory locking, not a new bug. [RESULTS.md](../../../RESULTS.md#one-cart-two-orders) has the numbers and the sources.
