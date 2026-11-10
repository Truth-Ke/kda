# Round Loop Prompt

You are running one KDA round in `<TASK_WORKSPACE>`.

## Contract

- Contract: `<CONTRACT_PATH>`
- Objective: `<OBJECTIVE>`
- Metric: `<METRIC_NAME>` (`<DIRECTION>`, aggregate with `<AGGREGATION>`)
- Workloads: partial `<PARTIAL_WORKLOADS>`, full `<FULL_WORKLOADS>`
- Budget: `<BUDGET_MODE>` (default `sota`: no hard cap, but record usage)
- Language/tools: `<LANGUAGE_AND_TOOLS>` (do not assume; use what the contract says)

Read `contracts/task.yaml`, `state.json`, `docs/handoff.md`, and the latest
`docs/process_log.md` before acting.

## Skills (load on demand)

Load only the skill for the current step; do not load every skill at startup.

- Candidate implementation: `kernel-triton-writing`, `kernel-cute-writing`, or
  `triton-kernels`, matching the contract's language.
- Code changes: `implement`; test-first work: `tdd`.
- Hard bug or regression: `diagnosing-bugs`.
- Profiling: `ncu-report-skill`.
- Review: `code-review`.
- Structured planning or a blocked decision: `to-spec`, `to-tickets`,
  `wayfinder`, `grill-me`/`grilling`, `domain-modeling`, `prototype`, or
  `codebase-design` only when the round reaches that gate.
- Session close: `handoff`; phase close: `retro`; docs: `writing-for-agents`.

A skill is reference, not authority. The contract and measured evidence win.
`deep-research`, `KernelWiki`, and `perf-optimization-casebook` belong to
research, not to a measurement round unless the round explicitly returns to
research.

## Process Record

Update `docs/process_log.md` with:

- the round objective and contract state;
- the hypotheses and their falsifiable predictions;
- each decision, the reasoning, alternatives considered, and evidence;
- every agent or subagent: task, inputs, outputs, tools, result, cost;
- failed attempts and rejected candidates.

Append structured events to `runs/<run_id>/agent_trace.jsonl` and record
`runs/<run_id>/usage.json` (wall time, GPU time, tokens, cost when known).
This is mandatory even when the budget is SOTA-first and uncapped.

## Round Steps

1. Choose at most three mechanism-different candidates. For each, record the
   hypothesis, prediction, parent, and expected bottleneck.
2. Snapshot the source to `artifacts/<candidate_id>/<code_hash>/` before the
   first run. Record `code_hash` and `snapshot_path` in `candidates.jsonl`.
3. **Correctness**: run the contract's independent validation. Update
   `validation_status` (`pass`, `partial`, `fail`, `not_run`).
4. **FAST**: quick measurement on the relevant workloads. Exploratory only.
5. **CONFIRM**: interleaved repeated measurement against the current champion
   or baseline, with consistent timing, cache, and compilation conventions.
   Mark differences inside `tie_threshold` as TIE.
6. **Profiler**: run only when needed (close result, failed prediction,
   unclear bottleneck, or a representation decision). Record the report path.
7. **FULL**: for a competitive candidate, cover all `full_workloads` and the
   required long-run correctness. A champion must pass FULL.
8. Rank with `python3 scripts/rank_round.py --workspace <TASK_WORKSPACE>`.
   Render `round_results.md` with `python3 scripts/summarize_round.py`.
9. Promote only with `rank_round.py --promote <candidate> --run-id <run>`.
   If rejected, record the reason; never delete the candidate silently.
10. Update `champions.json`, `state.json`, `docs/optimization_log.md`, and
    `docs/process_log.md`.
11. If the session ends, write `docs/handoff.md` with references to state and
    runs, not duplicated scores.

## Failure and Stagnation

- Use `diagnosing-bugs`: build a tight red-capable feedback loop, reproduce,
  minimise, generate 3-5 falsifiable hypotheses, change one variable at a
  time.
- If the same mechanisms repeat, record `RESEARCH_AGAIN` and return to
  research. Do not silently lower the bar.
- If the contract or oracle is wrong, stop and ask the user; do not rewrite it.

## Do Not

- Do not hand-write scores or bypass `rank_round.py`.
- Do not promote a FAST-only or incomplete candidate.
- Do not change the reference, tolerance, or workload to make a candidate pass.
- Do not claim an improvement inside the noise threshold.
- Do not skip the process log or usage record.
