# Copyright 2026 Co-developed by KDA (Kernel Design Agents)

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts import rank_round  # noqa: E402


CONTRACT = {
    "contract_version": 1,
    "validation": {
        "full_workloads": ["w1", "w2"],
        "partial_workloads": ["w1"],
    },
    "metric": {
        "name": "latency_ms",
        "direction": "lower_is_better",
        "aggregation": "geomean",
        "repeat_aggregation": "median",
        "tie_threshold": 0.03,
    },
}

HEADER = [
    "run_id", "round_id", "candidate_id", "phase", "workload_id",
    "shape_cluster", "dtype", "metric_name", "metric_value", "metric_unit",
    "direction", "baseline_run_id", "env_id", "latency_ms", "score",
    "command", "log_path", "timestamp", "notes",
]


def row(run_id, candidate, phase, workload, value, baseline="b0", round_id="r1"):
    return {
        "run_id": run_id,
        "round_id": round_id,
        "candidate_id": candidate,
        "phase": phase,
        "workload_id": workload,
        "shape_cluster": workload,
        "dtype": "float16",
        "metric_name": "latency_ms",
        "metric_value": str(value),
        "metric_unit": "ms",
        "direction": "lower_is_better",
        "baseline_run_id": baseline,
        "env_id": "env",
        "latency_ms": str(value),
        "score": "",
        "command": "bench",
        "log_path": "",
        "timestamp": "2026-11-10T00:00:00Z",
        "notes": "",
    }


class Workspace:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "contracts").mkdir()
        (self.root / "runs").mkdir()
        (self.root / "contracts" / "task.json").write_text(json.dumps(CONTRACT))

    def write_benchmark(self, rows):
        with (self.root / "benchmark.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=HEADER)
            writer.writeheader()
            writer.writerows(rows)

    def write_candidates(self, candidates):
        with (self.root / "candidates.jsonl").open("w") as handle:
            for candidate in candidates:
                handle.write(json.dumps(candidate) + "\n")

    def make_run(self, run_id, code_hash=None):
        run_dir = self.root / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        if code_hash:
            (run_dir / "code_hash.txt").write_text(code_hash + "\n")

    def cleanup(self):
        self.tmp.cleanup()


def candidate(candidate_id, status, code_hash=None):
    return {
        "candidate_id": candidate_id,
        "validation_status": status,
        "code_hash": code_hash or f"hash-{candidate_id}",
        "validation_run_ids": [f"run-{candidate_id}"],
    }


class RankRoundTests(unittest.TestCase):
    def setUp(self):
        self.ws = Workspace()

    def tearDown(self):
        self.ws.cleanup()

    def test_official_incomplete_unverified_and_exploratory(self):
        rows = [
            row("b0", "baseline", "CONFIRM", "w1", 10),
            row("r1", "c1", "CONFIRM", "w1", 8),
            row("r1", "c1", "CONFIRM", "w1", 8.2),
            row("r2", "c2", "CONFIRM", "w1", 8.1),
            row("r3", "c3", "FULL", "w1", 7),
            row("r4", "c4", "CONFIRM", "w1", 9),
            row("r5", "c5", "FAST", "w1", 6),
        ]
        self.ws.write_benchmark(rows)
        self.ws.write_candidates(
            [
                candidate("c1", "partial"),
                candidate("c2", "pass"),
                candidate("c3", "pass"),
                candidate("c4", "fail"),
                candidate("c5", "pass"),
            ]
        )
        self.ws.make_run("b0")
        self.ws.make_run("r1", "hash-c1")
        self.ws.make_run("r2", "hash-c2")
        ranking = rank_round.build_ranking(
            rank_round.read_benchmark(self.ws.root / "benchmark.csv"),
            rank_round.read_candidates(self.ws.root / "candidates.jsonl"),
            CONTRACT,
            self.ws.root,
        )
        official_ids = [item["candidate_id"] for item in ranking["official"]]
        self.assertEqual(official_ids, ["c1", "c2"])
        self.assertTrue(ranking["official"][1]["tie"])
        self.assertEqual([item["candidate_id"] for item in ranking["incomplete"]], ["c3"])
        self.assertEqual([item["candidate_id"] for item in ranking["unverified"]], ["c4"])
        self.assertEqual([item["candidate_id"] for item in ranking["exploratory"]], ["c5"])

    def test_promote_requires_full_trace_and_beats_tie_threshold(self):
        rows = [
            row("b0", "baseline", "FULL", "w1", 10),
            row("b0", "baseline", "FULL", "w2", 10),
            row("r6", "c6", "FULL", "w1", 7),
            row("r6", "c6", "FULL", "w2", 9),
            row("r7", "c7", "FULL", "w1", 7.1),
            row("r7", "c7", "FULL", "w2", 9.1),
        ]
        self.ws.write_benchmark(rows)
        self.ws.write_candidates([candidate("c6", "pass"), candidate("c7", "pass")])
        self.ws.make_run("b0")
        self.ws.make_run("run-c6")
        self.ws.make_run("run-c7")
        for run_id, candidate_id in (("r6", "c6"), ("r7", "c7")):
            self.ws.make_run(run_id, f"hash-{candidate_id}")
        (self.ws.root / "champions.json").write_text("{}\n")

        result = rank_round.promote(
            self.ws.root, "c6", "r6", CONTRACT,
            rank_round.read_benchmark(self.ws.root / "benchmark.csv"),
            rank_round.read_candidates(self.ws.root / "candidates.jsonl"),
        )
        self.assertEqual(result, 0)
        champions = json.loads((self.ws.root / "champions.json").read_text())
        self.assertEqual(champions["global"]["candidate_id"], "c6")

        result = rank_round.promote(
            self.ws.root, "c7", "r7", CONTRACT,
            rank_round.read_benchmark(self.ws.root / "benchmark.csv"),
            rank_round.read_candidates(self.ws.root / "candidates.jsonl"),
        )
        self.assertEqual(result, 1)

    def test_promote_refuses_hash_mismatch(self):
        self.ws.write_benchmark(
            [
                row("b0", "baseline", "FULL", "w1", 10),
                row("b0", "baseline", "FULL", "w2", 10),
                row("r6", "c6", "FULL", "w1", 7),
                row("r6", "c6", "FULL", "w2", 9),
            ]
        )
        self.ws.write_candidates([candidate("c6", "pass")])
        self.ws.make_run("b0")
        self.ws.make_run("run-c6")
        run_dir = self.ws.root / "runs" / "r6"
        run_dir.mkdir()
        (run_dir / "code_hash.txt").write_text("different\n")
        (self.ws.root / "champions.json").write_text("{}\n")
        result = rank_round.promote(
            self.ws.root, "c6", "r6", CONTRACT,
            rank_round.read_benchmark(self.ws.root / "benchmark.csv"),
            rank_round.read_candidates(self.ws.root / "candidates.jsonl"),
        )
        self.assertEqual(result, 1)


    def test_baseline_uses_referenced_run_not_all_runs(self):
        rows = [
            row("b0", "baseline", "CONFIRM", "w1", 10),
            row("b1", "baseline", "CONFIRM", "w1", 100),
            row("r1", "c1", "CONFIRM", "w1", 20, baseline="b0"),
        ]
        self.ws.write_benchmark(rows)
        self.ws.write_candidates([candidate("c1", "partial")])
        self.ws.make_run("b0")
        self.ws.make_run("b1")
        self.ws.make_run("r1", "hash-c1")
        ranking = rank_round.build_ranking(
            rank_round.read_benchmark(self.ws.root / "benchmark.csv"),
            rank_round.read_candidates(self.ws.root / "candidates.jsonl"),
            CONTRACT,
            self.ws.root,
        )
        official = ranking["official"][0]
        self.assertAlmostEqual(official["baseline_aggregate"], 10)
        self.assertAlmostEqual(official["vs_baseline"], 0.5)

    def test_first_promotion_compares_to_baseline(self):
        rows = [
            row("b0", "baseline", "FULL", "w1", 10),
            row("b0", "baseline", "FULL", "w2", 10),
            row("r8", "c8", "FULL", "w1", 20),
            row("r8", "c8", "FULL", "w2", 20),
        ]
        self.ws.write_benchmark(rows)
        self.ws.write_candidates([candidate("c8", "pass")])
        self.ws.make_run("b0")
        self.ws.make_run("run-c8")
        self.ws.make_run("r8", "hash-c8")
        (self.ws.root / "champions.json").write_text("{}\n")
        result = rank_round.promote(
            self.ws.root, "c8", "r8", CONTRACT,
            rank_round.read_benchmark(self.ws.root / "benchmark.csv"),
            rank_round.read_candidates(self.ws.root / "candidates.jsonl"),
        )
        self.assertEqual(result, 1)

    def test_official_requires_run_directory(self):
        self.ws.write_benchmark(
            [
                row("b0", "baseline", "CONFIRM", "w1", 10),
                row("r1", "c1", "CONFIRM", "w1", 8),
            ]
        )
        self.ws.write_candidates([candidate("c1", "partial")])
        self.ws.make_run("b0")
        ranking = rank_round.build_ranking(
            rank_round.read_benchmark(self.ws.root / "benchmark.csv"),
            rank_round.read_candidates(self.ws.root / "candidates.jsonl"),
            CONTRACT,
            self.ws.root,
        )
        self.assertEqual(ranking["official"], [])
        self.assertEqual(ranking["incomplete"][0]["candidate_id"], "c1")

    def test_official_requires_baseline_row(self):
        self.ws.write_benchmark([row("r1", "c1", "CONFIRM", "w1", 8)])
        self.ws.write_candidates([candidate("c1", "partial")])
        self.ws.make_run("b0")
        self.ws.make_run("r1", "hash-c1")
        ranking = rank_round.build_ranking(
            rank_round.read_benchmark(self.ws.root / "benchmark.csv"),
            rank_round.read_candidates(self.ws.root / "candidates.jsonl"),
            CONTRACT,
            self.ws.root,
        )
        self.assertEqual(ranking["official"], [])
        self.assertEqual(ranking["incomplete"][0]["candidate_id"], "c1")

    def test_promote_requires_validation_run(self):
        rows = [
            row("b0", "baseline", "FULL", "w1", 10),
            row("b0", "baseline", "FULL", "w2", 10),
            row("r9", "c9", "FULL", "w1", 7),
            row("r9", "c9", "FULL", "w2", 9),
        ]
        self.ws.write_benchmark(rows)
        item = candidate("c9", "pass")
        item["validation_run_ids"] = ["missing-validation"]
        self.ws.write_candidates([item])
        self.ws.make_run("b0")
        self.ws.make_run("r9", "hash-c9")
        (self.ws.root / "champions.json").write_text("{}\n")
        result = rank_round.promote(
            self.ws.root, "c9", "r9", CONTRACT,
            rank_round.read_benchmark(self.ws.root / "benchmark.csv"),
            rank_round.read_candidates(self.ws.root / "candidates.jsonl"),
        )
        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
