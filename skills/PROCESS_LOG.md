# Process Log

KDA records enough of the process to improve it later without copying the same
event into three places.

## Required Files

```text
docs/process_log.md             # per-round decisions and evidence links
runs/<run_id>/agent_trace.jsonl # key actions and actor handoffs
runs/<run_id>/usage.json        # time, tokens, GPU time, cost (unknown = null)
```

## `docs/process_log.md`

One section per round. Keep it brief: decisions, why, evidence links, failures,
next step. Do not paste logs or duplicate every score.

```markdown
## Round <n> - <date>

### Objective
<what this round is trying to learn or improve>

### Hypotheses
- H1: <hypothesis>; prediction: <falsifiable prediction>; outcome: <accepted/rejected/pending>
- H2: ...

### Decisions
- Decision: <what was chosen>
  - Why: <evidence and trade-offs>
  - Alternative: <what was not chosen and why>
  - Evidence: <run ids, benchmark rows, notes>

### Agents
- <actor>: <what it did that changed the work; result>
- <actor>: ...

### Candidates
- <candidate_id>: <mechanism, parent, status, key metric, run ids, reject reason>

### Failures and surprises
<failed builds, invalid candidates, noisy measurements, wrong assumptions>

### Next step
<the single next action and its owner>
```

## `runs/<run_id>/agent_trace.jsonl`

Append one JSON object per **key action**; do not log every tool call. Include
subagent dispatches and returns, because those are otherwise lost.

```json
{"ts":"2026-11-10T12:00:00Z","round_id":"round-01","actor":"main","action":"research","reason":"need prior art for tiling","inputs":["research/notes/tiling.md"],"outputs":["candidate:c001"],"run_id":null,"status":"ok"}
{"ts":"2026-11-10T12:05:00Z","round_id":"round-01","actor":"subagent:diagnosing-bugs","action":"build_feedback_loop","reason":"candidate c001 is slower than baseline","inputs":["benchmark.csv"],"outputs":["runs/r001"],"run_id":"r001","status":"ok"}
```

Fields: `actor` (`main`, `subagent:<name>`, `tool:<name>`), `action`, `reason`,
`inputs`, `outputs`, `run_id`, `status` (`ok`, `failed`, `skipped`, `blocked`).
Optional: `tokens`, `duration_s`, `cost_usd`. Unknown values may be `null`.

## `runs/<run_id>/usage.json`

`capture_run.py` writes the wall clock automatically; fill GPU time, tokens,
and cost when known, otherwise leave them `null`. SOTA-first work has no hard
budget cap, but the usage record is mandatory for later process optimization.

## Rules

- Record failed attempts and rejected candidates; they are evidence.
- Reference artifacts by path or run id; do not duplicate scores.
- The trace explains actions and handoffs; the process log explains decisions.
  Neither replaces `benchmark.csv`, `candidates.jsonl`, or `runs/`.
