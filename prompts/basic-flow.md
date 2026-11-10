# Kernel Design Agents Basic Flow Prompt

You are working in a task implementation workspace. Your job is to produce the best correct implementation for the task described below.

## Task Contract

- Task name: `<fill in>`
- Objective: `<fill in the user-facing goal>`
- Correctness requirements: `<fill in required behavior, tolerances, or invariants>`
- Workloads: `<fill in stable workload ids and the full set>`
- Target metric: `<name, direction, aggregation, noise threshold>`
- Performance or quality target: `<fill in measurable target if any>`
- Allowed implementation approaches: `<fill in languages, libraries, APIs, or constraints>`
- Budget mode: `<sota by default; record usage even when uncapped>`
- Validation command: `<fill in the command that proves correctness>`
- Evaluation command: `<fill in the command that measures the target, if different>`
- Promotion criteria: `<fill in what must be true before a candidate is accepted>`

## Workflow

1. Read the repository structure, existing implementation, tests, and task documentation.
2. Identify the baseline behavior and the validation path.
3. Research only the references needed for this task.
4. Write an implementation-plan draft to `docs/draft.md`.
5. Turn the draft into an executable plan before editing code.
6. Implement one candidate at a time.
7. Run validation after each meaningful candidate.
8. Record candidate results, parent relationships, and evidence in the workspace.
9. Record the overall process, the reasoning behind decisions, and each
   agent/subagent's actions in `docs/process_log.md` and
   `runs/<run_id>/agent_trace.jsonl`.
10. Keep the final change scoped to the task contract.

## Plan Draft Requirements

The draft in `docs/draft.md` should include:

- The current baseline and how it is validated.
- The main risks and unknowns.
- Candidate implementation directions ranked by expected value and risk.
- The first concrete implementation steps.
- The exact validation and evaluation commands to run.
- The evidence required to promote, revise, or reject a candidate.

Do not start implementation until the draft exists.
