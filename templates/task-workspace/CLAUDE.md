# Task Workspace Agent Instructions

This workspace is a KDA task. Read these first:

1. `contracts/task.yaml` - authoritative objective, workloads, metric, oracle,
   promotion rules, and budget mode.
2. `state.json` - current stage and next action.
3. `docs/handoff.md` - previous session's handoff, if any.
4. `docs/process_log.md` - overall process, reasoning, and agent record.

## Skills

The KDA skills are installed under `.claude/skills/`. Load only the skill for
the current phase; do not load every skill at startup. The phase gates are in
the KDA repository's `docs/agent-runtime.md`; briefly:

- Round 0: `research`, `deep-research`, `KernelWiki`,
  `perf-optimization-casebook`.
- Candidate: `kernel-triton-writing`, `kernel-cute-writing`, or
  `triton-kernels`, plus `implement`/`tdd` when changing code.
- Debug: `diagnosing-bugs`.
- Profile: `ncu-report-skill`.
- Review: `code-review`.
- Planning: `wayfinder`, `to-spec`, `to-tickets`, `grilling`, `domain-modeling`,
  `prototype`, `codebase-design`.
- User decision: `grill-me` (or `grilling` directly).
- Session close: `handoff`; phase close: `retro`; docs: `writing-for-agents`.

If a skill is missing, run:

```bash
python3 {{KDA_ROOT}}/scripts/install_skills.py --target .
```

## Execution

- Use `python3 {{KDA_ROOT}}/scripts/capture_run.py --run-id <id> --code <src> -- <command>`
  for measured runs.
- Use `python3 {{KDA_ROOT}}/scripts/rank_round.py --workspace .` to rank.
- Use `python3 {{KDA_ROOT}}/scripts/summarize_round.py --workspace .` to
  render the report.
- Promote only with `rank_round.py --promote <candidate> --run-id <run>`.
- Record the process, reasoning, and each agent/subagent action in
  `docs/process_log.md` and `runs/<run_id>/agent_trace.jsonl`.

## Boundaries

- Do not change the contract's oracle, tolerance, or workloads to make a
  candidate pass.
- Do not hand-write scores or promote an incomplete/FAST-only candidate.
- Do not invent hardware, a baseline, or a benchmark; ask when the operator
  environment is unknown.
- Keep the task-specific code and data in this workspace, not in the KDA
  repository.
