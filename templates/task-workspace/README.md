# Task Workspace: {{TASK_NAME}}

Objective: {{OBJECTIVE}}

Created: {{DATE}}

This workspace follows the KDA round workflow. The generic workflow lives in
the KDA repository; this directory owns task-specific code, data, measurements,
and artifacts.

## Start

1. Fill `contracts/task.yaml`; freeze the independent oracle and tolerances.
2. Run the baseline and capture it with `scripts/capture_run.py` (from KDA).
3. Write `docs/process_log.md` for Round 0 and record hypotheses.
4. Run the round loop from `prompts/round-loop.md`.
5. Rank with `scripts/rank_round.py`; promote only a FULL, fully validated,
   traceable candidate.

## Files

- `CLAUDE.md`: task-workspace agent instructions and skill gate pointers.
- `.claude/skills/`: installed KDA skills.
- `contracts/task.yaml`: authoritative task contract.
- `docs/process_log.md`: overall process, reasoning, and per-agent actions.
- `docs/plan.md`: executable plan.
- `docs/handoff.md`: cross-session handoff.
- `research/`: notes and sources.
- `src/`: candidate implementations.
- `artifacts/`: immutable candidate snapshots.
- `runs/`: one directory per measured run; `agent_trace.jsonl` and `usage.json`.
- `benchmark.csv`: standardized measurements.
- `candidates.jsonl`: candidate identity and validation status.
- `champions.json`: promoted champion index.
- `state.json`: recovery summary.
