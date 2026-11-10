# Round Engine

The round engine is a small, generic loop for performance-sensitive tasks. It
does not assume a hardware vendor, a kernel language, or a benchmark suite.
Those belong to the task contract.

## Round 0: Research

The runtime startup, phase gates, and subagent policy are in
`docs/agent-runtime.md`. Load only the skill for the current gate.

1. Read `contracts/task.yaml`, `state.json`, and `docs/handoff.md`.
2. Research the mechanism and prior art. Use KernelWiki, `research`, and
   `deep-research` when available; fall back to `research` if deep research
   is unavailable.
3. Write `research/notes/<topic>.md` with sources, and record the reasoning
   in `docs/process_log.md`.
4. Produce a Math/Schedule Top-3: three mechanism-different directions, each
   with a falsifiable prediction.
5. Record the research cost in `runs/<run_id>/usage.json` or the process log.

## Candidate

A candidate is a concrete implementation with:

- `candidate_id`, parent, source/mechanism, hypothesis, prediction;
- an immutable source snapshot at `artifacts/<candidate_id>/<code_hash>/`;
- a contract version and validation status.

Limit a round to three mechanism-different candidates. More candidates are
not automatically better; each needs an evidence path.

## Measurement Phases

- **FAST**: correctness on the relevant workloads and a quick timing check.
  Exploratory; never promoted.
- **CONFIRM**: interleaved repeated measurement against the current champion
  or baseline, with the same timing, cache, and compilation conventions.
  Differences inside the noise threshold are `TIE`.
- **FULL**: the full workload distribution from the contract plus the required
  correctness checks. A champion must pass FULL.

Profiler runs are on demand: use them when a result is close, a prediction
fails, a bottleneck is unclear, or a lower-level representation is being
considered. Do not profile every candidate by default.

## Ranking and Promotion

Run `python3 scripts/rank_round.py --workspace <workspace>`. It produces
`round_ranking.json` and separates `official`, `incomplete`, `unverified`, and
`exploratory`. Render a report with `scripts/summarize_round.py`.

Promote only with `rank_round.py --promote`; it enforces FULL coverage,
validation, traceability, and the tie threshold. If no champion exists yet,
the candidate must beat the traceable baseline. Record rejected candidates and
the reason in `candidates.jsonl` and `docs/optimization_log.md`.

## Stopping

Stop a round when:

- a candidate is promoted and the champion is stable across FULL;
- the remaining hypotheses are falsified or blocked;
- the contract's promotion criteria are met;
- a human checkpoint decides to stop.

Do not stop because a single FAST run looks good. If the process is stalled,
record `RESEARCH_AGAIN` and go back to research rather than silently changing
the measurement rules.

## Budget

Default `budget.mode: sota`: no hard cap. Record detailed usage anyway:
wall time, GPU time, tokens, cost estimate, and what was measured versus
estimated. `budget.mode: capped` is available when a task wants a hard limit;
only then does `on_exhaustion` stop or ask.

## Process Record

Every round updates `docs/process_log.md` with the objective, hypotheses,
decisions and reasoning, alternatives, agents/subagents and what they did,
candidate outcomes, failures, and next step. Append structured events to
`runs/<run_id>/agent_trace.jsonl`. This record is the input to later process
optimization; it is not optional.

## Checkpoints

Ask the user only when the decision is theirs:

- after Round 0's Math/Schedule Top-3;
- before moving to a lower-level representation;
- before final delivery;
- when the direction conflicts or a hard budget is exhausted.

Keep the brief to one screen: conclusion, evidence, options, recommendation.
