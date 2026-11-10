# Prompt Templates

This directory stores generic prompts for the Kernel Design Agents workflow.

The templates are intentionally task-agnostic. Fill in the task objective,
constraints, validation command, and promotion criteria before starting an
agent session in a separate implementation workspace.

## Available Templates

| Path | Purpose |
|---|---|
| `basic-flow.md` | Minimal prompt for research, planning, implementation, validation, and iteration. |
| `research-first.md` | Round 0: research, source grading, and Math/Schedule Top-3. |
| `round-loop.md` | One round: candidates, FAST/CONFIRM/FULL, ranking, promotion, and process record. |

## How To Use

1. Create or enter the task implementation workspace.
2. Copy the relevant template content into the agent session.
3. Replace placeholders with task-specific details.
4. Ask the agent to read the workspace and write `docs/draft.md` or the
   process log.
5. Convert that draft into an executable plan.
6. Run the implementation loop with validation after each meaningful change.

Task-specific prompts should live with the task they describe. Do not add
benchmark-specific datasets, acceptance tables, or private evaluator details to
this generic repository.

## Process Record

`research-first.md` and `round-loop.md` require the agent to record the overall
process, the reasoning behind decisions, and each agent/subagent's actions in
`docs/process_log.md` and `runs/<run_id>/agent_trace.jsonl`. See
`skills/PROCESS_LOG.md` for the format.
