# Evidence Model

KDA separates exploration from promotion. Exploration may be incomplete; the
official ranking and champion promotion require complete, validated, traceable
evidence.

## Task Contract

`contracts/task.yaml` is the authority for correctness, workloads, metric, and
promotion. The fields `rank_round.py` reads:

```yaml
contract_version: 1

validation:
  command: <independent oracle command>
  tolerance: <per-dtype tolerance>
  full_workloads: [<workload_id>, ...]
  partial_workloads: [<workload_id>, ...]

metric:
  name: latency_ms
  direction: lower_is_better        # or higher_is_better
  aggregation: geomean              # mean | median | geomean | min | max
  repeat_aggregation: median
  tie_threshold: 0.03

budget:
  mode: sota                        # sota | capped
  unit: gpu_minutes
  per_round: null
  total: null
  on_exhaustion: stop_and_handoff
  record_usage: true

baseline:
  candidate_id: baseline
  run_id: <baseline run id>
```

Promotion rules are fixed, not contract switches: FULL coverage, full
validation, traceable runs and code hashes, and an improvement beyond
`tie_threshold`.

Fields are conventions, not a strict schema. Missing optional fields fall back
to the defaults in `rank_round.py`; missing required fields produce warnings,
not a hard validation framework.

`rank_round.py` reads YAML when PyYAML is available. If PyYAML is not
installed, keep the same contract as JSON (`contracts/task.json`); the script
reads JSON with the standard library.

## `benchmark.csv`

One row per `(candidate, phase, workload, repeat)`:

```text
run_id, round_id, candidate_id, phase, workload_id, shape_cluster, dtype,
metric_name, metric_value, metric_unit, direction, baseline_run_id, env_id,
latency_ms, score, command, log_path, timestamp, notes
```

- `phase`: `FAST`, `CONFIRM`, or `FULL`.
- `workload_id`: a stable id from the contract, not a raw shape string.
- `baseline_run_id`: same environment and workload; required for official
  comparison. The ranking looks up the baseline by this run id, workload, and
  `env_id`; it does not aggregate every baseline row in the file.
- `env_id`: points to `runs/<run_id>/env.json` or an environment fingerprint.
- `metric_value` is the only value used for aggregation. `latency_ms` and
  `score` are human-readable derived columns and do not rank candidates.

## `candidates.jsonl`

```text
candidate_id, parent_id, source_id, hypothesis, prediction, code_path,
code_hash, snapshot_path, contract_version, validation_status,
validation_run_ids, measurement_scope, status, reject_reason
```

`validation_status`:

- `pass`: all `validation.full_workloads` passed.
- `partial`: the measured subset passed, but the full set is not complete.
- `fail`: at least one measured workload failed.
- `not_run`: no validation yet.

`status`: `research`, `validated`, `measured`, `promoted`, or `rejected`.

## Run Directory

```text
runs/<run_id>/
  command.txt
  stdout.log
  stderr.log
  env.json
  result.json
  code_hash.txt
  usage.json
  agent_trace.jsonl
```

The run directory is the execution fact. `benchmark.csv` is the standardized
measurement derived from it. Each run records `code_hash.txt`; a mismatch with
`candidates.jsonl` makes the old measurement stale.

## Ranking States

`rank_round.py` classifies each candidate/phase:

- `exploratory`: `FAST`, or not covering this phase's declared workload set.
- `unverified`: a measured workload failed, or validation is `not_run`/`fail`,
  or there is no `run_id`/`code_hash`.
- `incomplete`: missing a required workload or `baseline_run_id`.
- `official`: `CONFIRM` covers `partial_workloads` with `pass` or `partial`
  validation; `FULL` covers `full_workloads` with `pass` validation. Both
  require traceable runs.

Only `official` rows enter the official table. All sections are always
reported; `incomplete`, `unverified`, and `exploratory` are visible for
diagnosis but never for promotion.

Ranking is scoped: CONFIRM rows are ranked against other CONFIRM rows with the
same workload set, and FULL rows against other FULL rows with the same workload
set. A CONFIRM result and a FULL result are not placed in one ranked list.

## Aggregation

1. Repeats for the same `(candidate, phase, workload)` are aggregated with
   `repeat_aggregation` (default median); stdev is kept for context.
2. Workloads are aggregated with `metric.aggregation`.
3. Direction-aware comparison: `lower_is_better` uses `baseline/current`;
   `higher_is_better` uses `current/baseline`. A ratio above 1 is better.
4. Differences below `tie_threshold` are marked `TIE`; do not claim an
   improvement.

## Promotion

`rank_round.py --promote <candidate> --run-id <run>` writes
`champions.json` only when all of these hold:

- a `FULL` run covering `validation.full_workloads`;
- `validation_status=pass`, and `validation_run_ids` is non-empty with each
  validation run directory present;
- `run_id` and `code_hash` are traceable, and `runs/<run_id>/code_hash.txt`
  matches `candidates.jsonl`; if a workload was measured in a different run,
  that run's hash must match too;
- the candidate beats the current champion by more than `tie_threshold`; if no
  champion exists yet, it must beat the traceable baseline instead.

Champion entries are indexes; `runs/` and `benchmark.csv` remain the facts.

## Recovery Precedence

When records disagree:

1. `runs/` execution facts.
2. `benchmark.csv` standardized measurements.
3. `champions.json` and `state.json` indexes.
4. `handoff.md` narrative.

A changed `code_path` with a different `code_hash` marks old rows `stale`;
rerun or restore from `artifacts/<candidate_id>/<code_hash>/`. Do not silently
overwrite history.

## Budget and Process Record

SOTA-first is the default: no hard cap, but every run records
`usage.json` (wall time, GPU time, tokens, cost when known) and every
round updates `state.json.budget_used`. The process record is defined in
`skills/PROCESS_LOG.md`: `docs/process_log.md` plus
`runs/<run_id>/agent_trace.jsonl`.
