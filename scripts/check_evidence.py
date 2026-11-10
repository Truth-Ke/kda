#!/usr/bin/env python3
"""Advisory evidence check using the same readers as rank_round.py.

Prints warnings; never blocks exploration or promotion.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts import rank_round  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--benchmark", type=Path, help="default: <workspace>/benchmark.csv")
    parser.add_argument("--candidates", type=Path, help="default: <workspace>/candidates.jsonl")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    benchmark = args.benchmark or workspace / "benchmark.csv"
    candidates_path = args.candidates or workspace / "candidates.jsonl"
    if not benchmark.exists():
        raise SystemExit(f"benchmark not found: {benchmark}")

    rows = rank_round.read_benchmark(benchmark)
    candidates = rank_round.read_candidates(candidates_path)
    warnings: list[str] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        candidate_id = row["candidate_id"]
        phase = (row.get("phase") or "").strip().upper()
        key = (candidate_id, phase)
        if key in seen:
            continue
        seen.add(key)
        if candidate_id == "baseline":
            continue
        candidate = candidates.get(candidate_id)
        if candidate is None:
            warnings.append(f"candidate {candidate_id} absent from candidates.jsonl")
            continue
        warnings.extend(
            f"{candidate_id} {phase}: {reason}"
            for reason in rank_round.run_trace_reasons(
                workspace, candidate_id, phase, rows, candidate
            )
        )
        for item in rank_round.candidate_rows(rows, candidate_id, phase):
            baseline_run = item.get("baseline_run_id")
            if baseline_run and not (workspace / "runs" / baseline_run).exists():
                warnings.append(
                    f"{candidate_id} {phase}: baseline run runs/{baseline_run} is missing"
                )

    for warning in sorted(set(warnings)):
        print(f"warning: {warning}", file=sys.stderr)
    print(f"{len(set(warnings))} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
