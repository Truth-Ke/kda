#!/usr/bin/env python3
"""Render a human-readable round report from round_ranking.json."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def fmt(value) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.6g}"
    return str(value)


def table(items: list[dict]) -> list[str]:
    lines = [
        "| rank | candidate | phase | aggregate | vs baseline | status | notes |",
        "|---:|---|---|---:|---:|---|---|",
    ]
    for index, item in enumerate(items, 1):
        notes = "; ".join(item.get("reasons") or [])
        if item.get("tie"):
            notes = (notes + "; TIE" if notes else "TIE")
        lines.append(
            f"| {item.get('rank', index)} | {item['candidate_id']} | "
            f"{item['phase']} | {fmt(item.get('aggregate'))} | "
            f"{fmt(item.get('vs_baseline'))} | {item.get('status', '')} | {notes} |"
        )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--ranking", type=Path, help="default: <workspace>/round_ranking.json")
    parser.add_argument("--out", type=Path, help="default: <workspace>/round_results.md")
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    ranking_path = args.ranking or workspace / "round_ranking.json"
    if not ranking_path.exists():
        raise SystemExit(f"ranking not found: {ranking_path}")
    ranking = json.loads(ranking_path.read_text(encoding="utf-8"))
    out = args.out or workspace / "round_results.md"

    metric = ranking.get("metric", {})
    lines = [
        "# Round Results",
        "",
        f"- Generated: {ranking.get('generated_at', 'unknown')}",
        f"- Metric: `{metric.get('name', 'metric')}` "
        f"({metric.get('direction', 'unknown')}, {metric.get('aggregation', 'unknown')})",
        f"- Workloads: partial={ranking.get('workloads', {}).get('partial', [])}, "
        f"full={ranking.get('workloads', {}).get('full', [])}",
        "",
        "## Official",
        "",
    ]
    official = ranking.get("official", [])
    if official:
        scopes: dict[str, list[dict]] = {}
        for item in official:
            scopes.setdefault(item.get("scope", item["phase"]), []).append(item)
        for scope, items in scopes.items():
            lines += [f"### {scope}", ""]
            lines.extend(table(items))
            lines.append("")
    else:
        lines.append("No official candidates.")
    lines += ["", "## Incomplete", ""]
    incomplete = ranking.get("incomplete", [])
    lines.extend(table(incomplete) if incomplete else ["None."])
    lines += ["", "## Unverified", ""]
    unverified = ranking.get("unverified", [])
    lines.extend(table(unverified) if unverified else ["None."])
    lines += ["", "## Exploratory", ""]
    exploratory = ranking.get("exploratory", [])
    lines.extend(table(exploratory) if exploratory else ["None."])
    lines += [
        "",
        "> Only the official table is eligible for champion promotion. "
        "Incomplete and unverified results remain visible for diagnosis.",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
