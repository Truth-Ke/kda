# Agent Instructions

This repository is the generic Kernel Design Agents workflow reference. It should stay small and task-agnostic.

## Repository Rules

- Use English for repository-facing files, comments, documentation, prompts, and commit messages.
- Keep task-specific prompts, datasets, validators, generated implementations, benchmark logs, and candidate artifacts out of this repository.
- Treat benchmark competitions, including MLSys-style work, as downstream applications of KDA rather than as the scope of this repository.
- Put generated outputs in `runs/`, `outputs/`, or `profile/`; these paths are ignored by git.
- Prefer documenting reusable workflow mechanics over documenting one task's private harness or acceptance thresholds.
- First-party workflow mechanics live in `docs/`, `prompts/`, `templates/`, and `scripts/`. Vendored skills live in `skills/` and keep their upstream licenses.

## Navigation

- Minimal flow: `docs/agent-flow.md`.
- Round engine: `docs/round-engine.md`.
- Evidence, ranking, and promotion: `docs/evidence-model.md`.
- Research protocol: `docs/research-protocol.md`.
- Skill routing: `docs/skill-routing.md`.
- Agent runtime and phase gates: `docs/agent-runtime.md`.
- Process record: `skills/PROCESS_LOG.md`.
- Prompt templates: `prompts/research-first.md`, `prompts/round-loop.md`.
- Workspace skeleton: `templates/task-workspace/`.

## Expected Agent Workflow

For a new task:

1. Create or enter a separate implementation workspace.
2. Define the task contract: objective, constraints, validation command, workloads, metric, promotion criteria, and budget mode.
3. Install the vendored skills with `scripts/install_skills.py`.
4. Use `prompts/research-first.md` for Round 0 and `prompts/round-loop.md` for later rounds.
5. Read local task code and documentation before proposing implementation changes.
6. Write the initial plan draft to `docs/draft.md` inside the task workspace.
7. Convert the draft into an executable plan.
8. Implement in small iterations, validating each meaningful candidate.
9. Record candidate relationships, evaluation results, and profiling evidence when applicable.
10. Record the overall process, reasoning, and per-agent actions in `docs/process_log.md` and `runs/<run_id>/agent_trace.jsonl`.
11. Keep this repository focused on the reusable flow.

## Optional Skills

Vendored skills are under `skills/` and installed into a workspace's
`.claude/skills/` by `scripts/install_skills.py`. Use `docs/skill-routing.md`
to choose one. Do not load every skill at once.

- `humanize` remains an optional external plugin for plan generation.
- `research` and `deep-research` cover background and literature work.
- `diagnosing-bugs` covers performance regressions and hard bugs.
- Kernel writing skills cover the language the task contract permits.
- `wayfinder`, `to-spec`, `to-tickets`, `retro`, `loop-me`, `implement`,
  `grill-me`, `grilling`, `domain-modeling`, `prototype`, and `codebase-design`
  are model-loadable but phase-gated decision/process tools.
  Load them at the gate in `docs/skill-routing.md`, not at session start.
