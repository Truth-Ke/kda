# Vendored Skills

This directory contains skills used by the KDA workflow. They are vendored so
a task workspace can install them without depending on an external skills
repository. Each skill keeps its upstream license and records its source in
`SOURCE.yaml` and its changes in `ADAPTATION.md`.

## Layout

```text
skills/
  behavior/      # research, planning, debugging, review, handoff
  kernel/        # Triton, CuTe, performance casebook, HF Triton
  research/      # deep-research (CC BY-NC 4.0)
  KernelWiki/    # pinned git submodule, installed directly
  ncu-report-skill/  # pinned git submodule
```

## Install into a workspace

From the KDA repository:

```bash
python3 scripts/install_skills.py --target /path/to/task-workspace
```

This creates `.claude/skills/<name>` links in the workspace and writes
`skills.lock.json`. Use `--copy` when symlinks are not available. The KDA
repository can install its own skills with:

```bash
python3 scripts/install_skills.py --target .
```

`.claude/skills/` is a local installation artifact and is ignored by git.

## Invocation policy

All vendored skills are **model-loadable**: the `disable-model-invocation`
key is omitted, so the agent can reach them. Loading is phase-gated by
`../docs/skill-routing.md`: do not load a decision or process skill outside
its gate without a user checkpoint.

- Round/runtime skills: `research`, `deep-research`, `diagnosing-bugs`, `tdd`,
  `writing-for-agents`, `code-review`, kernel writing skills.
- Decision/process skills: `wayfinder`, `to-spec`, `to-tickets`, `retro`,
  `loop-me`, `implement`, `grill-me`, `grilling`, `domain-modeling`,
  `prototype`, `codebase-design`, `handoff`. Load them at the matching phase,
  not at session start.
- The user can still invoke any skill explicitly by name.

## Process record

Every skill follows `PROCESS_LOG.md`: record the overall process, the reasoning
behind decisions, and what each agent or subagent did. The task workspace
keeps `docs/process_log.md` and `runs/<run_id>/agent_trace.jsonl`.

The `KernelWiki` and `ncu-report-skill` submodules are third-party and are not
edited; the workflow prompt still requires the process record when they are
used.

## Precedence

The task contract and independent validation are authoritative. A skill may
suggest an implementation or measurement approach, but it must not override
the contract's oracle, tolerances, workloads, or performance metric.

## Licenses

- Behavior skills: MIT, Copyright (c) 2026 Matt Pocock.
- NVIDIA kernel skills: Apache-2.0, Copyright (c) 2011-2026 NVIDIA Corporation.
- Hugging Face `triton-kernels`: Apache-2.0.
- `deep-research`: CC BY-NC 4.0, Copyright 2026 Cheng-I Wu. It is not covered
  by KDA's first-party license and carries a non-commercial restriction.
- `KernelWiki` and `ncu-report-skill`: MIT; see `THIRD_PARTY_NOTICES.md` for
  artifact-specific terms.

See `THIRD_PARTY_NOTICES.md` and `third_party_licenses/` for the verbatim
license texts.
