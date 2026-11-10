# Agent Runtime

This document defines how the agent runs a KDA task: what it reads at startup,
when it loads each vendored skill, and how subagents are used.

## Startup Sequence

Run the agent session in the task workspace, not in the KDA repository.

1. Read `CLAUDE.md` in the task workspace.
2. Read `contracts/task.yaml`, `state.json`, and `docs/handoff.md`.
3. Read the latest `docs/process_log.md` section and `skills.lock.json`.
4. Confirm `.claude/skills/` exists; if not, run
   `python3 <kda>/scripts/install_skills.py --target .`.
5. Load only the skill for the current phase (table below). Do not load every
   skill at startup.

## Main Agent and Subagents

The main agent owns the contract, state, ranking, promotion, and process
record. It is the only actor that writes `champions.json`, `state.json`, and
the final decision.

Subagents are optional and scoped:

- Use them for research (`research`, `deep-research`), profiling
  (`ncu-report-skill`), or review (`code-review`).
- Start each with a fresh context window.
- Give the subagent the contract excerpt, the specific question, relevant run
  ids/paths, and the required output format.
- The subagent returns findings; the main agent records a
  `subagent:<name>` event in `runs/<run_id>/agent_trace.jsonl` and updates
  `docs/process_log.md`.
- Subagents do not promote candidates, edit `champions.json`, or rewrite the
  contract.

## Phase Gates

Load a skill when the workflow reaches its gate. The gate is a phase, not a
keyword.

| Phase | Load | Purpose | Output |
|---|---|---|---|
| Session start | none | Read `contracts/task.yaml`, `state.json`, and `docs/handoff.md` directly | context |
| Large/ambiguous effort | `wayfinder` | Decision map and tickets | `docs/wayfinder/` |
| Turn decisions into a spec | `to-spec` | Spec | `.scratch/specs/` |
| Slice a spec | `to-tickets` | Tracer-bullet tickets | `.scratch/tickets/` |
| User decision needed | `grill-me` / `grilling` | Interview the user; do not answer for them | decision notes |
| Domain terminology or ADR | `domain-modeling` | Glossary/ADR updates |
| Throwaway design probe | `prototype` | Disposable artifact; not a candidate |
| Module/interface/seam design | `codebase-design` | Design vocabulary |
| Round 0 research | `research` | Targeted source work | `research/notes/` |
| Broad/literature research | `deep-research` | Multi-mode research | `research/` + sources |
| Kernel knowledge lookup | `KernelWiki` | Mechanism/prior art | notes with provenance |
| Optimization precedent | `perf-optimization-casebook` | Prior optimization patterns | candidate hypotheses |
| Write a Triton kernel | `kernel-triton-writing` | Triton implementation | candidate code |
| Write a CuTe kernel | `kernel-cute-writing` | CuTe implementation | candidate code |
| Portable Triton patterns | `triton-kernels` | Cross-vendor Triton guidance | candidate code |
| Implement a ticket | `implement` | Scoped implementation | code |
| Test-first change | `tdd` | Red-green loop | tests |
| Hard bug/regression | `diagnosing-bugs` | Tight feedback loop + hypotheses | diagnosis |
| Profile a kernel | `ncu-report-skill` | Profiler report analysis | profile summary |
| Review a change | `code-review` | Standards + spec review | findings |
| Write docs/prompts | `writing-for-agents` | Agent-facing document style | docs |
| Session close | `handoff` | Handoff document | `docs/handoff.md` |
| Phase close | `retro` | Environment/process retrospective | improvements |
| Design a workflow | `loop-me` | Workflow spec | `docs/workflows/` |

## Loading Mechanics

- Invoke a skill with the Skill tool using its exact name, for example
  `kernel-triton-writing` or `deep-research`.
- Project skills are discovered from `.claude/skills/<name>/SKILL.md`.
- If a scoped name such as `kda:code-review` is shown but fails, use the
  unscoped name (`code-review`); the task workspace resolves the project skill.
- If a skill is not found, run `install_skills.py --target .` and check
  `skills.lock.json`. The links point at the KDA checkout; rerun the installer
  if the KDA repository moves.
- If a skill was just installed or its invocation metadata changed, start a
  new agent session; the current session may cache the old skill metadata.
- Load one or two skills at a time. Loading every skill at startup is context
  pollution, not thoroughness.
- A skill is reference, not authority: the task contract and measured evidence
  win.

## Round Execution

1. Read the contract and state.
2. Load the gate skill(s) for the current step.
3. Do the step; record reasoning and agent actions in
   `docs/process_log.md` and `runs/<run_id>/agent_trace.jsonl`.
4. Measure with the contract's validation/evaluation commands.
5. Rank with `scripts/rank_round.py`; summarize with
   `scripts/summarize_round.py`.
6. Promote only through `rank_round.py --promote`.
7. At session close, load `handoff`; at phase close, load `retro`.

## Checkpoints

Ask the user when the decision is theirs:

- Round 0 Math/Schedule Top-3;
- before a lower-level representation;
- before final delivery;
- a contract conflict or a budget-mode decision.

Use `grill-me` for the interview, then record the decision in the process log.

## Failure

- If a skill's advice conflicts with the contract, record the conflict and
  follow the contract.
- If a skill is missing or fails to load, record it, install it, or fall back
  to the documented alternative; do not silently skip the process record.
- If the task is blocked on the operator environment, stop and ask; do not
  invent a hardware or benchmark.
