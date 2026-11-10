# Research Protocol

Research is how KDA avoids guessing. It is not a separate phase that must be
exhaustive before any code; it is a budgeted activity that feeds a candidate.

## Research Levels

- **Local**: read the task code, contract, existing notes, and nearby docs.
  Usually minutes. Always start here.
- **Targeted**: one mechanism, paper, repository, or API question. Use the
  `research` skill; write `research/notes/<topic>.md`.
- **Deep**: a broad or contested question, a literature scan, or a systematic
  comparison. Use the vendored `deep-research` skill when its modes fit; it is
  CC BY-NC 4.0 and is not covered by KDA's first-party license. For KDA
  mechanism scans, default to `three-way-scan` or `lit-review`; use the full
  report or systematic-review mode only when the user asks for it.

If deep research is unavailable, too slow, or a poor fit, fall back to
`research` plus KernelWiki. Record `research_fallback_reason` in the note or
process log; do not block the round.

## Sources

Rank sources:

- **A**: official documentation, source code, specifications, first-party API
  references, or the task's own contract and oracle.
- **B**: peer-reviewed papers, maintainer design docs, reproducible technical
  reports.
- **C**: blog posts, forum answers, secondary summaries. Useful for leads, not
  for correctness claims.

Every source record includes URL, commit/tag for code, and access date. Prefer
a pinned commit over `main`. Record this in `research/notes/sources.yaml` or a
source table in the note.

## What to Record

For each research pass:

- the question and why it matters;
- what was searched and what was excluded;
- the mechanism, not just the paper's headline result;
- applicability conditions and counterexamples;
- the resulting candidate direction or the reason none was chosen;
- cost and duration.

Update `docs/process_log.md` with the reasoning and each subagent's task and
result. Append structured events to `runs/<run_id>/agent_trace.jsonl` when the
research is tied to a run.

## Research and the Contract

Research can suggest a metric, workload, or verification method, but the task
contract is authoritative. Do not change the oracle, tolerance, or workload
set to make a research idea score better. If the research reveals that the
contract is wrong, record the issue and ask the user; do not silently rewrite
it.

## Representation Choices

Research may compare implementation substrates (for example a high-level DSL
versus a lower-level language). Record the choice and its evidence in
`docs/process_log.md` or a dedicated decision note. Do not assume a substrate:
the contract and the measured bottleneck decide. A lower-level representation
is justified by a falsifiable opportunity, not by preference.

## Search Stagnation

If the same mechanisms keep appearing:

1. Re-read KernelWiki and the task's prior failures.
2. Change the question, not just the query.
3. Try a mechanism-different candidate or an equivalence search if the task
   has algebraic structure.
4. Record `RESEARCH_AGAIN` and the reason. Do not silently keep sampling.
