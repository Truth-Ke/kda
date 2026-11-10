# Agent Flow

Kernel Design Agents is a repeatable loop for agent-driven implementation work. The loop is useful when a task needs both exploration and evidence-based promotion decisions.

## Principle

Keep the reusable workflow separate from the task workspace. This repository explains the flow. The task workspace owns code, tests, datasets, benchmark scripts, private rules, and generated artifacts.

MLSys-style benchmark work is one possible application of this loop. The same flow can also be used for compiler passes, runtime kernels, infrastructure changes, or other performance-sensitive tasks.

## Minimal Loop

1. Define the task contract.
2. Let the agent inspect the local workspace.
3. Make the agent write `docs/draft.md`.
4. Convert the draft into an executable plan.
5. Implement the first candidate.
6. Validate correctness.
7. Measure the target metric when applicable.
8. Record evidence and decide whether to keep, revise, or reject the candidate.
9. Repeat until the promotion criteria are met or the remaining blockers are explicit.

## Extended Flow

For work that needs repeated candidates and evidence-based promotion, use the
extended flow:

- `docs/round-engine.md`: Round 0, candidate, FAST/CONFIRM/FULL, ranking,
  promotion, budget, and checkpoints.
- `docs/evidence-model.md`: task contract fields, CSV/JSONL records, ranking
  states, aggregation, snapshots, and recovery precedence.
- `docs/research-protocol.md`: Local/Targeted/Deep research, source grading,
  fallback, and representation decisions.
- `docs/skill-routing.md`: which vendored skill to load for which situation.
- `prompts/research-first.md` and `prompts/round-loop.md`: executable templates.
- `skills/PROCESS_LOG.md`: required process, reasoning, and per-agent record.

The extended flow keeps the same principle: the task workspace owns code,
data, measurements, and artifacts; this repository owns reusable mechanics.

## Task Contract

Each task should state:

- Objective.
- Inputs and outputs.
- Correctness requirements and the independent oracle.
- Workload ids and the partial/full sets.
- Target metric, direction, aggregation, and noise threshold.
- Constraints on implementation language, dependencies, APIs, or deployment.
- Validation command.
- Evaluation command, if different from validation.
- Promotion criteria.
- Budget mode (`sota` by default) and usage records.

## Evidence Records

Use simple files in the task workspace:

- `docs/draft.md` for the first plan draft.
- `docs/plan.md` for the executable plan.
- `docs/process_log.md` for the overall process, reasoning, and per-agent record.
- `benchmark.csv` or another tabular log for measurable results.
- `candidates.jsonl` for candidate names, parent links, validation, and status.
- `artifacts/<candidate_id>/<code_hash>/` for immutable candidate snapshots.
- `runs/<run_id>/` for command, logs, environment, code hash, usage, and
  `agent_trace.jsonl`.
- `profile/` for profiler output or report summaries.
- `champions.json` and `state.json` for indexes and recovery.

See `docs/evidence-model.md` for the field conventions.

The exact format is less important than consistency. A future reader should be able to reconstruct what changed, what was measured, and why a candidate was promoted.

## Promotion Rule

Promote a candidate only when it satisfies the task contract, passes the full
validation set, has a traceable FULL run, and has evidence that it improves or
preserves the target metric beyond the noise threshold. If a candidate is
rejected, record the reason instead of silently discarding it. Use
`scripts/rank_round.py --promote`; do not hand-edit `champions.json`.
