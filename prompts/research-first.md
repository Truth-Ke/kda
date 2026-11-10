# Research-First Prompt (Round 0)

You are starting Round 0 for a KDA task. Your job is to understand the problem,
the prior art, and the mechanism space before proposing candidates.

## Inputs

- Task workspace: `<TASK_WORKSPACE>`
- Task contract: `<CONTRACT_PATH>`
- Hardware/software: `<HARDWARE_SOFTWARE>` (free text; do not assume a vendor)
- Implementation language: `<LANGUAGE>`
- Budget: `<BUDGET_MODE>` (default `sota`: no hard cap, but record usage)

## Required Reads

1. `contracts/task.yaml`, `state.json`, and `docs/handoff.md`.
2. Existing code and tests in the workspace.
3. `research/notes/` and any prior `docs/process_log.md`.
4. The relevant KernelWiki entry points, if available.

## Skills (load on demand)

Load only the skill for the step you are doing; do not load every skill at
startup.

- `research` for targeted primary-source work; `deep-research` when the
  question needs a broad or multi-mode scan.
- `KernelWiki` for mechanism and prior-art lookup.
- `perf-optimization-casebook` when a known optimization pattern may apply.
- `grill-me` only if a decision needs the user (pilot, hardware, budget).
- `writing-for-agents` when writing the research note or process log.
- Do not load kernel-writing skills yet; they belong to the candidate step.

If a skill is missing, check `.claude/skills/` and run `install_skills.py`.

## Work

1. Restate the objective, inputs/outputs, correctness requirements, and the
   target metric in your own words.
2. Research the mechanism and prior art at the level the question needs:
   Local, Targeted, or Deep. Use `research`; use `deep-research` when its
   modes fit, preferring `three-way-scan` or `lit-review` for a kernel
   mechanism scan; use the full report mode only when the user asks. If deep
   research is unavailable, fall back and record why.
3. Rank sources A/B/C and pin code sources to commits. Write
   `research/notes/<topic>.md` and a source table.
4. Produce a Math/Schedule Top-3: three mechanism-different directions. For
   each, state the mechanism, applicability, expected bottleneck, a
   falsifiable prediction, and the cheapest experiment that would falsify it.
5. Record everything in `docs/process_log.md`: the questions, what was
   searched, what was excluded, the reasoning, each subagent's task and
   result, and the cost.
6. Stop before implementing. Present a one-screen brief: conclusion,
   evidence, options, recommendation.

## Constraints

- Do not change the contract, oracle, tolerances, or workload set to fit a
  research idea.
- Do not propose a lower-level representation without a falsifiable
  opportunity; "it might be faster" is not enough.
- Do not claim a performance improvement without a measured run.
- Do not skip the process log; it is the input to later process optimization.

## Output

- `research/notes/<topic>.md`
- `docs/process_log.md` (Round 0 section)
- A short Math/Schedule Top-3 with predictions
- `state.json` updated with the next action
