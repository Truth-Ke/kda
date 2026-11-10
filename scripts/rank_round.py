#!/usr/bin/env python3
"""Rank a KDA round and gate champion promotion.

The script joins ``benchmark.csv`` (measurements) with ``candidates.jsonl``
(candidate identity and validation status) and the task contract (metric
direction, aggregation, workload sets, promotion rules). Exploration rows are
kept visible; only complete, validated, traceable rows enter the official
ranking.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

PHASES = {"FAST", "CONFIRM", "FULL"}
OFFICIAL_PHASES = {"CONFIRM", "FULL"}


def load_contract(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"contract not found: {path}")
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    try:
        import yaml  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            f"PyYAML is required to read {path}; install PyYAML or use a .json contract"
        ) from exc
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SystemExit(f"contract must be a mapping: {path}")
    return data


def read_benchmark(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"benchmark not found: {path}")
    rows: list[dict] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader, start=2):
            if not row.get("candidate_id") or not row.get("workload_id"):
                print(f"warning: skipping incomplete row at line {index}", file=sys.stderr)
                continue
            try:
                value = float(row.get("metric_value", ""))
            except (TypeError, ValueError):
                print(f"warning: skipping non-numeric metric at line {index}", file=sys.stderr)
                continue
            row = dict(row)
            row["_metric_value"] = value
            rows.append(row)
    return rows


def read_candidates(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    candidates: dict[str, dict] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            print(f"warning: bad candidates.jsonl line {line_number}: {exc}", file=sys.stderr)
            continue
        if isinstance(item, dict) and item.get("candidate_id"):
            candidates[item["candidate_id"]] = item
    return candidates


def aggregate(values: list[float], method: str) -> float:
    if not values:
        raise ValueError("cannot aggregate an empty list")
    if method == "mean":
        return statistics.fmean(values)
    if method == "median":
        return statistics.median(values)
    if method == "min":
        return min(values)
    if method == "max":
        return max(values)
    if method == "geomean":
        if any(value <= 0 for value in values):
            raise ValueError("geomean requires positive values")
        return math.exp(statistics.fmean(math.log(value) for value in values))
    raise ValueError(f"unknown aggregation: {method}")


def contract_metric(contract: dict) -> dict:
    metric = contract.get("metric") or {}
    return {
        "name": metric.get("name", "metric"),
        "direction": metric.get("direction", "lower_is_better"),
        "aggregation": metric.get("aggregation", "geomean"),
        "repeat_aggregation": metric.get("repeat_aggregation", "median"),
        "tie_threshold": float(metric.get("tie_threshold", 0.03)),
    }


def workload_sets(contract: dict, rows: list[dict]) -> tuple[set[str], set[str]]:
    validation = contract.get("validation") or {}
    all_workloads = {row["workload_id"] for row in rows}
    partial = set(validation.get("partial_workloads") or [])
    full = set(validation.get("full_workloads") or [])
    if not partial:
        partial = full or all_workloads
    if not full:
        full = partial
    return partial, full


def group_measurements(rows: list[dict]) -> dict[tuple[str, str, str], list[float]]:
    groups: dict[tuple[str, str, str], list[float]] = {}
    for row in rows:
        phase = (row.get("phase") or "").strip().upper()
        if phase not in PHASES:
            print(f"warning: unknown phase {phase!r}; row ignored", file=sys.stderr)
            continue
        key = (row["candidate_id"], phase, row["workload_id"])
        groups.setdefault(key, []).append(row["_metric_value"])
    return groups


def candidate_rows(rows: list[dict], candidate_id: str, phase: str) -> list[dict]:
    return [
        row
        for row in rows
        if row["candidate_id"] == candidate_id
        and (row.get("phase") or "").strip().upper() == phase
    ]


def run_trace_reasons(
    workspace: Path,
    candidate_id: str,
    phase: str,
    rows: list[dict],
    candidate: dict,
) -> list[str]:
    reasons: list[str] = []
    code_hash = candidate.get("code_hash")
    for row in candidate_rows(rows, candidate_id, phase):
        run_id = row.get("run_id")
        if not run_id:
            reasons.append("missing run_id")
            continue
        run_dir = workspace / "runs" / run_id
        if not run_dir.exists():
            reasons.append(f"missing run directory runs/{run_id}")
            continue
        hash_file = run_dir / "code_hash.txt"
        if not hash_file.exists():
            reasons.append(f"missing runs/{run_id}/code_hash.txt")
            continue
        if code_hash and hash_file.read_text(encoding="utf-8").strip() != code_hash:
            reasons.append(f"code_hash mismatch for runs/{run_id}")
    return sorted(set(reasons))


def baseline_value_for_workload(
    rows: list[dict],
    metric: dict,
    candidate_id: str,
    phase: str,
    workload: str,
    baseline_id: str,
    workspace: Path,
) -> float | None:
    refs: list[float] = []
    seen: set[tuple[str, str]] = set()
    for row in candidate_rows(rows, candidate_id, phase):
        if row["workload_id"] != workload:
            continue
        baseline_run_id = row.get("baseline_run_id")
        if not baseline_run_id:
            continue
        env_id = row.get("env_id") or ""
        key = (baseline_run_id, env_id)
        if key in seen:
            continue
        seen.add(key)
        if not (workspace / "runs" / baseline_run_id).exists():
            continue
        matches = [
            item
            for item in rows
            if item.get("run_id") == baseline_run_id
            and item["candidate_id"] == baseline_id
            and item["workload_id"] == workload
            and (not env_id or item.get("env_id") == env_id)
        ]
        refs.extend(item["_metric_value"] for item in matches)
    if not refs:
        return None
    return aggregate(refs, metric["repeat_aggregation"])


def baseline_for_candidate(
    rows: list[dict],
    metric: dict,
    candidate_id: str,
    phase: str,
    workloads: set[str],
    baseline_id: str,
    workspace: Path,
) -> tuple[float | None, dict[str, float | None]]:
    per_workload = {
        workload: baseline_value_for_workload(
            rows, metric, candidate_id, phase, workload, baseline_id, workspace,
        )
        for workload in sorted(workloads)
    }
    if any(value is None for value in per_workload.values()):
        return None, per_workload
    values = list(per_workload.values())
    return aggregate(values, metric["aggregation"]), per_workload


def classify(
    candidate_id: str,
    phase: str,
    candidate: dict | None,
    rows: list[dict],
    groups: dict[tuple[str, str, str], list[float]],
    partial: set[str],
    full: set[str],
    contract: dict,
    workspace: Path,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if phase == "FAST" or phase not in OFFICIAL_PHASES:
        return "exploratory", ["FAST is exploratory"]
    required = full if phase == "FULL" else partial
    available = {
        workload
        for (cid, p, workload) in groups
        if cid == candidate_id and p == phase
    }
    missing = sorted(required - available)
    if missing:
        return "incomplete", [f"missing workload: {', '.join(missing)}"]
    if candidate is None:
        return "unverified", ["candidate is absent from candidates.jsonl"]
    status = (candidate.get("validation_status") or "not_run").lower()
    if status in {"fail", "not_run"}:
        return "unverified", [f"validation_status={status}"]
    if phase == "FULL" and status != "pass":
        return "unverified", ["FULL requires validation_status=pass"]
    if phase == "CONFIRM" and status not in {"pass", "partial"}:
        return "unverified", [f"validation_status={status}"]
    if not candidate.get("code_hash"):
        return "unverified", ["no code_hash in candidates.jsonl"]
    trace_reasons = run_trace_reasons(workspace, candidate_id, phase, rows, candidate)
    if trace_reasons:
        return "incomplete", trace_reasons
    baseline_id = (contract.get("baseline") or {}).get("candidate_id", "baseline")
    _, baseline_by_workload = baseline_for_candidate(
        rows, contract_metric(contract), candidate_id, phase, required,
        baseline_id, workspace,
    )
    missing_baseline = [w for w, value in baseline_by_workload.items() if value is None]
    if missing_baseline:
        return "incomplete", [
            f"missing baseline for workload: {', '.join(missing_baseline)}"
        ]
    return "official", reasons


def summarize_candidate(
    candidate_id: str,
    phase: str,
    rows: list[dict],
    groups: dict[tuple[str, str, str], list[float]],
    metric: dict,
    required: set[str],
) -> dict:
    per_workload: dict[str, dict] = {}
    for workload in sorted(required):
        values = groups.get((candidate_id, phase, workload), [])
        if not values:
            continue
        per_workload[workload] = {
            "aggregate": aggregate(values, metric["repeat_aggregation"]),
            "repeats": len(values),
            "stdev": statistics.pstdev(values) if len(values) > 1 else 0.0,
        }
    aggregates = [item["aggregate"] for item in per_workload.values()]
    overall = aggregate(aggregates, metric["aggregation"]) if aggregates else None
    return {
        "candidate_id": candidate_id,
        "phase": phase,
        "metric": metric["name"],
        "direction": metric["direction"],
        "aggregate": overall,
        "workloads": per_workload,
    }


def relative_to_baseline(current: float, baseline: float | None, direction: str) -> float | None:
    if baseline is None or current == 0:
        return None
    if direction == "lower_is_better":
        return baseline / current
    return current / baseline


def build_ranking(
    rows: list[dict],
    candidates: dict[str, dict],
    contract: dict,
    workspace: Path,
) -> dict:
    metric = contract_metric(contract)
    partial, full = workload_sets(contract, rows)
    groups = group_measurements(rows)
    baseline_id = (contract.get("baseline") or {}).get("candidate_id", "baseline")
    sections: dict[str, list[dict]] = {
        "official": [],
        "incomplete": [],
        "unverified": [],
        "exploratory": [],
    }
    candidate_ids = sorted({cid for (cid, _, _) in groups if cid != baseline_id})
    for candidate_id in candidate_ids:
        for phase in sorted({p for (cid, p, _) in groups if cid == candidate_id}):
            status, reasons = classify(
                candidate_id, phase, candidates.get(candidate_id), rows, groups,
                partial, full, contract, workspace,
            )
            required = full if phase == "FULL" else partial
            item = summarize_candidate(
                candidate_id, phase, rows, groups, metric,
                required if status == "official" else {
                    workload for (cid, p, workload) in groups
                    if cid == candidate_id and p == phase
                },
            )
            item["status"] = status
            item["reasons"] = reasons
            item["baseline_aggregate"], item["baseline_workloads"] = baseline_for_candidate(
                rows, metric, candidate_id, phase,
                set(item["workloads"].keys()), baseline_id, workspace,
            )
            item["vs_baseline"] = relative_to_baseline(
                item["aggregate"], item["baseline_aggregate"], metric["direction"],
            ) if item["aggregate"] is not None else None
            sections[status].append(item)

    reverse = metric["direction"] == "higher_is_better"
    phase_order = {"CONFIRM": 0, "FULL": 1}
    direction = -1 if reverse else 1
    for items in sections.values():
        items.sort(
            key=lambda item: (
                phase_order.get(item["phase"], 9),
                item["aggregate"] is None,
                direction * (item["aggregate"] or 0.0),
            )
        )

    # Rank only within a comparable scope: same phase and same workload set.
    groups_by_scope: dict[tuple[str, tuple[str, ...]], list[dict]] = {}
    for item in sections["official"]:
        item["scope"] = f"{item['phase']}:{','.join(sorted(item['workloads']))}"
        groups_by_scope.setdefault(
            (item["phase"], tuple(sorted(item["workloads"]))), []
        ).append(item)
    for items in groups_by_scope.values():
        items.sort(key=lambda item: item["aggregate"] or 0.0, reverse=reverse)
        for index, item in enumerate(items):
            item["rank"] = index + 1
            if index == 0:
                item["tie"] = False
                continue
            best = items[0]["aggregate"]
            current = item["aggregate"]
            item["tie"] = bool(
                best and current is not None
                and abs(current - best) / abs(best) < metric["tie_threshold"]
            )
    sections["official"].sort(
        key=lambda item: (phase_order.get(item["phase"], 9), item.get("rank", 999))
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metric": metric,
        "workloads": {"partial": sorted(partial), "full": sorted(full)},
        **sections,
    }


def read_champions(path: Path) -> dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def promote(
    workspace: Path,
    candidate_id: str,
    run_id: str,
    contract: dict,
    rows: list[dict],
    candidates: dict[str, dict],
) -> int:
    metric = contract_metric(contract)
    partial, full = workload_sets(contract, rows)
    groups = group_measurements(rows)
    if candidate_id not in candidates:
        print(f"refusing promotion: unknown candidate {candidate_id}", file=sys.stderr)
        return 1
    candidate = candidates[candidate_id]
    status, reasons = classify(
        candidate_id, "FULL", candidate, rows, groups, partial, full, contract,
        workspace,
    )
    if status != "official":
        print(
            f"refusing promotion: {candidate_id} is {status} ({'; '.join(reasons)})",
            file=sys.stderr,
        )
        return 1
    validation_runs = candidate.get("validation_run_ids") or []
    if not validation_runs:
        print("refusing promotion: no validation_run_ids", file=sys.stderr)
        return 1
    for validation_run in validation_runs:
        if not (workspace / "runs" / validation_run).exists():
            print(
                f"refusing promotion: validation run directory runs/{validation_run} is missing",
                file=sys.stderr,
            )
            return 1
    full_rows = candidate_rows(rows, candidate_id, "FULL")
    run_ids = {row.get("run_id") for row in full_rows if row.get("run_id")}
    if run_id not in run_ids:
        print(f"refusing promotion: run_id={run_id} is not a FULL run for {candidate_id}", file=sys.stderr)
        return 1
    summary = summarize_candidate(candidate_id, "FULL", rows, groups, metric, full)
    if summary["aggregate"] is None:
        print("refusing promotion: no aggregate", file=sys.stderr)
        return 1

    champions_path = workspace / "champions.json"
    champions = read_champions(champions_path)
    champion = champions.get("global")
    new = summary["aggregate"]
    if champion and champion.get("metric_value") is not None:
        old = float(champion["metric_value"])
        comparison = "champion"
    else:
        baseline_id = (contract.get("baseline") or {}).get("candidate_id", "baseline")
        old, _ = baseline_for_candidate(
            rows, metric, candidate_id, "FULL", full, baseline_id, workspace,
        )
        comparison = "baseline"
    if old is None:
        print(
            "refusing promotion: no champion and no traceable baseline to compare against",
            file=sys.stderr,
        )
        return 1
    improvement = (
        (old - new) / old if metric["direction"] == "lower_is_better"
        else (new - old) / old
    )
    if improvement <= metric["tie_threshold"]:
        print(
            f"refusing promotion: improvement over {comparison} {improvement:.2%} "
            f"is within tie_threshold {metric['tie_threshold']:.2%}",
            file=sys.stderr,
        )
        return 1

    entry = {
        "candidate_id": candidate_id,
        "run_id": run_id,
        "code_hash": candidate["code_hash"],
        "metric_name": metric["name"],
        "metric_value": summary["aggregate"],
        "direction": metric["direction"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    champions["global"] = entry
    workloads = champions.setdefault("workloads", {})
    workload_runs: dict[str, str] = {}
    for row in full_rows:
        workload = row["workload_id"]
        if row.get("run_id") and workload not in workload_runs:
            workload_runs[workload] = row["run_id"]
    for workload, value in summary["workloads"].items():
        workloads[workload] = {
            **entry,
            "run_id": workload_runs.get(workload, run_id),
            "metric_value": value["aggregate"],
        }
    champions_path.write_text(json.dumps(champions, indent=2) + "\n", encoding="utf-8")
    print(f"promoted {candidate_id} with run {run_id}")
    return 0


def print_summary(ranking: dict) -> None:
    for section in ("official", "incomplete", "unverified", "exploratory"):
        items = ranking[section]
        print(f"\n{section}: {len(items)}")
        for item in items[:10]:
            value = item["aggregate"]
            value_text = f"{value:.6g}" if value is not None else "n/a"
            extra = f" rank={item.get('rank')}" if item.get("rank") else ""
            if item.get("scope"):
                extra += f" scope={item['scope']}"
            tie = " TIE" if item.get("tie") else ""
            print(f"  {item['candidate_id']} {item['phase']} {value_text}{extra}{tie}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--contract", type=Path, help="default: <workspace>/contracts/task.yaml")
    parser.add_argument("--benchmark", type=Path, help="default: <workspace>/benchmark.csv")
    parser.add_argument("--candidates", type=Path, help="default: <workspace>/candidates.jsonl")
    parser.add_argument("--round-id", help="only include rows from this round")
    parser.add_argument("--json-out", type=Path, help="default: <workspace>/round_ranking.json")
    parser.add_argument("--promote", help="candidate_id to promote")
    parser.add_argument("--run-id", help="FULL run_id backing the promotion")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    contract_path = args.contract or workspace / "contracts" / "task.yaml"
    benchmark_path = args.benchmark or workspace / "benchmark.csv"
    candidates_path = args.candidates or workspace / "candidates.jsonl"
    contract = load_contract(contract_path)
    rows = read_benchmark(benchmark_path)
    candidates = read_candidates(candidates_path)
    if args.round_id:
        rows = [row for row in rows if row.get("round_id") == args.round_id]

    if args.promote:
        if not args.run_id:
            raise SystemExit("--promote requires --run-id")
        return promote(workspace, args.promote, args.run_id, contract, rows, candidates)

    ranking = build_ranking(rows, candidates, contract, workspace)
    out = args.json_out or workspace / "round_ranking.json"
    out.write_text(json.dumps(ranking, indent=2) + "\n", encoding="utf-8")
    print_summary(ranking)
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
