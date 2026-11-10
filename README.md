# Kernel Design Agents

Kernel Design Agents (KDA) is an agent-centric workflow for using coding agents to research, implement, verify, and iterate on performance-sensitive kernel and operator tasks. It is intentionally independent of a single hardware vendor, language, or benchmark suite; a task contract supplies those choices.

This repository documents an early research prototype and remains under active development. Community feedback and contributions are welcome. If you are interested in HAN Lab Mafia's solutions ranking #1–3 on tracks at the MLSys Kernel Contest, see [mit-han-lab/mlsys2026-flashinfer-contest](https://github.com/mit-han-lab/mlsys2026-flashinfer-contest) for performance evaluation and reproduction.

**Agents: read [How Claude Uses KDA](#how-claude-uses-kda) first.** It is the runtime contract for task workspaces.

## Contents

| Path | Purpose |
|---|---|
| `docs/agent-flow.md` | Minimal end-to-end KDA workflow. |
| `docs/round-engine.md` | Round 0, candidates, FAST/CONFIRM/FULL, ranking, promotion, budget, checkpoints. |
| `docs/evidence-model.md` | Task contract fields, evidence records, ranking states, snapshots, recovery. |
| `docs/research-protocol.md` | Local/Targeted/Deep research, source grading, fallback, representation choices. |
| `docs/skill-routing.md` | Which vendored skill to load for which situation. |
| `docs/agent-runtime.md` | Startup sequence, phase gates, main-agent/subagent policy, and skill loading mechanics. |
| `prompts/README.md` | How to use prompt templates. |
| `prompts/basic-flow.md` | Generic starter prompt for a new task. |
| `prompts/research-first.md` | Round 0 research prompt. |
| `prompts/round-loop.md` | Generic one-round prompt. |
| `templates/task-workspace/` | Task workspace skeleton. |
| `scripts/install_skills.py` | Install vendored skills into `.claude/skills/`. |
| `scripts/new_task.py` | Create a task workspace from the template. |
| `scripts/rank_round.py` | Rank a round and gate champion promotion. |
| `scripts/summarize_round.py` | Render `round_results.md`. |
| `scripts/check_evidence.py` | Advisory evidence warnings. |
| `scripts/capture_run.py` | Capture a command into `runs/<run_id>/`. |
| `skills/` | Vendored skills with source and license records. |
| `CLAUDE.md` | Repository-facing agent instructions. |
| `CONTRIBUTING.md` | Contribution process and DCO sign-off requirements. |
| `THIRD_PARTY_NOTICES.md` | Third-party component and license disclosures. |
| `third_party_licenses/` | Verbatim upstream license files for distributed third-party components. |

## Community Kernel Wishlist

Have a kernel that needs optimization? [Submit a request](https://github.com/NVlabs/kda/tree/wishlist#submit) directly as a pull request to `wishlist`, with a reproducible definition, representative workloads, and your best-known baseline implementation. No issue is required. The community wishlist currently supports NVIDIA B200 and B300 GPUs only.

[Browse and upvote requests](https://github.com/NVlabs/kda/pulls?q=is%3Apr%20base%3Awishlist), [discuss an idea](https://github.com/NVlabs/kda/issues/new?title=%5Bwishlist%5D%20) if you need help preparing the files, or visit the [project website](https://nvlabs.github.io/kda/). Keep request details in `requests/<github-username>-<kernel-name>/README.md` and use the [wishlist PR template](.github/PULL_REQUEST_TEMPLATE/wishlist.md) for the short description. Merging records the request, while optimization progress and result links remain on the original pull request. Website source lives on `pages`; the PR template and issue chooser settings are maintained on `main`.

## Getting Started
Install the agent workflow dependencies before starting the agent session:

```bash
git clone --recurse-submodules https://github.com/NVlabs/kda.git
cd kda

# install the vendored skills into this repository's .claude/skills/
python3 scripts/install_skills.py --target .

# create a separate task workspace and install the same skills there
python3 scripts/new_task.py /path/to/task-workspace --task-name my-kernel
```

`.claude/skills/` is a local installation artifact and is ignored by git. Use
`--copy` with `install_skills.py` when symlinks are not available.

Use KernelWiki from this repository's pinned submodule. A direct upstream
checkout may contain artifact snapshots governed by additional terms that are
omitted from this distribution.

## How Claude Uses KDA

This section is the runtime contract for an agent working in a task workspace.

### 1. Read before acting

In the task workspace, read in this order:

1. `CLAUDE.md` (task instructions and skill gates).
2. `contracts/task.yaml` (objective, workloads, oracle, metric, promotion,
   budget).
3. `state.json` (stage, round, next action).
4. `docs/handoff.md` (previous session; read the file directly, do not invoke
   the handoff skill at startup).
5. `docs/process_log.md` and `skills.lock.json`.

### 2. Install skills once

```bash
# create a task workspace from the template (also installs skills)
python3 /path/to/kda/scripts/new_task.py /path/to/task-workspace --task-name my-kernel

# or install into an existing workspace
python3 /path/to/kda/scripts/install_skills.py --target .
```

This creates `.claude/skills/<name>` and `skills.lock.json`. All vendored
skills are model-loadable; load only the one for the current phase. If a
scoped name such as `kda:code-review` fails, use the unscoped name
(`code-review`).

### 3. Load skills on demand

| Phase | Load |
|---|---|
| Round 0 research | `research`, `deep-research`, `KernelWiki`, `perf-optimization-casebook` |
| Candidate implementation | `kernel-triton-writing`, `kernel-cute-writing`, or `triton-kernels`; `implement`/`tdd` for code changes |
| Debug/regression | `diagnosing-bugs` |
| Profiling | `ncu-report-skill` |
| Review | `code-review` |
| Planning/decisions | `wayfinder`, `to-spec`, `to-tickets`, `grilling`, `domain-modeling`, `prototype`, `codebase-design`, `grill-me` |
| Session close | `handoff` |
| Phase close | `retro` |
| Documentation | `writing-for-agents` |

Do not load every skill at startup. A skill is reference, not authority: the
task contract, independent oracle, and measured evidence win.

### 4. Run the loop

```bash
# capture a measured run (creates runs/<run_id>/)
python3 /path/to/kda/scripts/capture_run.py --run-id <id> --code src -- <command>

# rank the round and gate promotion
python3 /path/to/kda/scripts/rank_round.py --workspace .

# render the report
python3 /path/to/kda/scripts/summarize_round.py --workspace .

# optional advisory evidence check
python3 /path/to/kda/scripts/check_evidence.py --workspace .

# promote only after FULL, full validation, traceable runs and a real gain
python3 /path/to/kda/scripts/rank_round.py --workspace . --promote <candidate> --run-id <run>
```

Use `FAST` for exploration, `CONFIRM` for interleaved comparison, and `FULL`
for the contract's full workload set. Only `FULL` candidates can be promoted.
The first promotion is compared against the traceable baseline when no
champion exists.

### 5. Record the process

Keep `docs/process_log.md` brief (decisions, reasoning, failures, next step),
append key actions to `runs/<run_id>/agent_trace.jsonl`, and let
`capture_run.py` write `usage.json`. Subagents return findings; the main agent
records what they did and owns promotion.

### 6. Boundaries

- Do not change the oracle, tolerance, or workload set to make a candidate
  pass.
- Do not hand-write scores or promote incomplete/FAST-only candidates.
- Do not assume a hardware vendor, language, or benchmark; the contract
  supplies them.
- `deep-research` defaults to `three-way-scan`/`lit-review` for mechanism
  scans; use full report mode only when the user asks.

## Submodules

The following third-party projects are included as Git submodules. The source URLs and revisions below are intentional and match the gitlinks recorded in this repository.

| Path | Source | Pinned revision | License |
|---|---|---|---|
| `skills/KernelWiki` | [mit-han-lab/KernelWiki](https://github.com/mit-han-lab/KernelWiki.git) | Based on [`76d27b56f804e7e7295d4c570e1e5d7eef4b0a75`](https://github.com/mit-han-lab/KernelWiki/commit/76d27b56f804e7e7295d4c570e1e5d7eef4b0a75), with the repository-maintained release sanitization recorded by the gitlink | MIT for original material; embedded artifacts retain their upstream terms; restricted CuTe DSL artifacts are omitted |
| `skills/ncu-report-skill` | [mit-han-lab/ncu-report-skill](https://github.com/mit-han-lab/ncu-report-skill.git) | [`d1887948c7d53690cfe6605f59c1329b8a1c6bb5`](https://github.com/mit-han-lab/ncu-report-skill/commit/d1887948c7d53690cfe6605f59c1329b8a1c6bb5) | MIT |

These submodules are not covered by this repository's first-party license. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the applicable license text and additional details.

## Vendored Skills

`skills/` also contains vendored behavior and kernel skills. They are not
covered by KDA's first-party license; each directory keeps its own `LICENSE`,
`SOURCE.yaml`, and `ADAPTATION.md`. See [skills/README.md](skills/README.md)
for the inventory and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for
license details.

The `deep-research` skill is **CC BY-NC 4.0** (non-commercial) and is not
covered by KDA's Apache-2.0/CC-BY-4.0 terms. Downstream users must preserve
its license and attribution.

Install the `humanize` Claude Code plugin from the Claude Code plugin UI:

```text
/plugin marketplace add PolyArch/humanize
/plugin install humanize@PolyArch
```

## Minimal Flow

1. Create a separate implementation workspace for the target task.
2. Define the task contract: objective, constraints, validation command, workloads, metric, and promotion criteria.
3. Start an agent session in the implementation workspace.
4. Give the agent `prompts/basic-flow.md`, filled in with the task-specific details; use `prompts/research-first.md` and `prompts/round-loop.md` for the extended flow.
5. Ask the agent to write a short plan draft to `docs/draft.md` in the implementation workspace.
6. Convert the draft into an executable plan, either manually or with a planning tool such as Humanize.
7. Implement in small iterations, verifying after each meaningful change.
8. Record candidates, benchmark or evaluation results, profiling evidence, and final promotion decisions.
9. Keep the process record in `docs/process_log.md` and `runs/<run_id>/agent_trace.jsonl`.

The workflow is intentionally independent of any single benchmark harness or hardware target. A downstream task can add its own evaluator, datasets, profiling tools, and domain-specific references.

For the extended round flow, see `docs/round-engine.md`, `docs/evidence-model.md`, and `prompts/round-loop.md`.

Validated CuTe candidates can be [exported as Hugging Face kernels](docs/huggingface-export.md).

## Recommended Workspace Layout

Use this repository as reference material, then do implementation work elsewhere:

```text
task-workspace/
  CLAUDE.md                # task agent instructions and skill gates
  .claude/skills/          # installed by scripts/install_skills.py
  contracts/
    task.yaml
  docs/
    draft.md
    plan.md
    process_log.md         # overall process, reasoning, per-agent record
    handoff.md
    wayfinder/
  research/
    notes/
  src/
  artifacts/               # immutable candidate snapshots
  runs/                    # one directory per measured run
  profile/
  benchmark.csv
  candidates.jsonl
  champions.json
  state.json
```

The exact files can change by domain. The important rule is that the agent records enough context for another engineer to understand what was tried, what passed validation, and why the final candidate was selected.

## Contributing

This project accepts outside contributions under the Developer Certificate of Origin process. See [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## License

Except for the third-party submodules identified above, first-party documentation, prompts, skills-style content, and assets are licensed under the [Creative Commons Attribution 4.0 International License](LICENSE), and first-party source code is licensed under the [Apache License 2.0](LICENSE).
