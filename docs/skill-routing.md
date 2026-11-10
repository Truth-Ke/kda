# Skill Routing

Load only the skill the current situation needs. The task contract and
independent validation are authoritative over any skill's advice.

The executable loading sequence, main-agent/subagent policy, and phase gates
are in `docs/agent-runtime.md`.

## Where Skills Live

Vendored skills are under `skills/`. Install them into a task workspace with:

```bash
python3 scripts/install_skills.py --target /path/to/task-workspace
```

This creates `.claude/skills/<name>` links and `skills.lock.json`. See
`skills/README.md` for the inventory and licenses.

## Routing Table

| Situation | Skill | Output |
|---|---|---|
| Large, ambiguous upgrade spanning sessions | `wayfinder` | `docs/wayfinder/map.md` + decision tickets |
| Turn the discussion into a spec | `to-spec` | `.scratch/specs/<name>.md` |
| Break a spec into slices | `to-tickets` | `.scratch/tickets/*.md` |
| Implement a ticket | `implement` / `tdd` | code + tests |
| Hard bug or performance regression | `diagnosing-bugs` | tight feedback loop + 3-5 falsifiable hypotheses |
| Background research | `research` | `research/notes/<topic>.md` |
| Broad literature/mechanism scan | `deep-research` | `research/` report + sources |
| User decision needed | `grill-me` / `grilling` | interview notes + decision |
| Domain terminology or ADR | `domain-modeling` | glossary/ADR updates |
| Throwaway design probe | `prototype` | disposable artifact, not a candidate |
| Module/interface/seam design | `codebase-design` | design vocabulary |
| Write a Triton kernel | `kernel-triton-writing` | candidate code |
| Write a CuTe kernel when the contract permits it | `kernel-cute-writing` | candidate code |
| Portable cross-vendor Triton patterns | `triton-kernels` | candidate code |
| Find a prior optimization pattern | `perf-optimization-casebook` | candidate hypothesis |
| Write docs or prompts | `writing-for-agents` | agent-facing documentation |
| Review a change | `code-review` | standards + spec findings |
| Session close | `handoff` | `docs/handoff.md` |
| Phase retrospective | `retro` | environment improvements |
| Design a recurring workflow | `loop-me` | `docs/workflows/*.md` |
| Pilot/operator/budget decision | `grill-me` | interview notes + decision |
| Kernel knowledge lookup | `KernelWiki` (submodule) | `research/notes/` with provenance |
| Profiler report analysis | `ncu-report-skill` | profile summary |

## Invocation Policy

All vendored skills are model-loadable: the `disable-model-invocation` key is
omitted, so the agent can reach them. Loading is phase-gated: load a skill
when the workflow reaches its row in the table, not at session start. The user can still invoke any skill explicitly.

- Round/runtime: `research`, `deep-research`, `diagnosing-bugs`, `tdd`,
  `writing-for-agents`, `code-review`, kernel writing skills.
- Decision/process: `wayfinder`, `to-spec`, `to-tickets`, `retro`, `loop-me`,
  `implement`, `grill-me`, `grilling`, `domain-modeling`, `prototype`,
  `codebase-design`, `handoff`. Load only at their phase gate or when the user
  asks; do not let them derail a measurement round.

## Contract Precedence

A skill may recommend an implementation, measurement, or reference setup. When
it conflicts with the task contract:

1. The contract's oracle, tolerance, workloads, and metric win.
2. Do not modify the reference or oracle to make a candidate pass.
3. Do not silently weaken a test or change a workload.
4. Record the conflict and the adaptation in `ADAPTATION.md` or the process log.

Two concrete examples:

- NVIDIA `kernel-triton-writing` suggests matching TF32 in `reference_fn` if
  verification fails. KDA forbids changing the contract's reference; fix the
  candidate or the implementation instead.
- HF `triton-kernels` assumes contiguous tensors. If the contract includes
  strides, write stride-aware code or record a contract limitation; do not
  silently call `.contiguous()`.

## Process Record

Every skill follows `skills/PROCESS_LOG.md`: record the overall process, the
reasoning behind decisions, and what each agent or subagent did in
`docs/process_log.md` and `runs/<run_id>/agent_trace.jsonl`.
