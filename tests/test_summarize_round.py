# Copyright 2026 Co-developed by KDA (Kernel Design Agents)

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts import summarize_round  # noqa: E402


class SummarizeRoundTests(unittest.TestCase):
    def test_writes_sections_and_tie_note(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ranking = {
                "generated_at": "2026-11-10T00:00:00Z",
                "metric": {
                    "name": "latency_ms",
                    "direction": "lower_is_better",
                    "aggregation": "geomean",
                },
                "workloads": {"partial": ["w1"], "full": ["w1", "w2"]},
                "official": [
                    {
                        "candidate_id": "c1",
                        "phase": "CONFIRM",
                        "aggregate": 8.1,
                        "vs_baseline": 1.23,
                        "rank": 1,
                        "tie": False,
                        "reasons": [],
                        "status": "official",
                    }
                ],
                "incomplete": [],
                "unverified": [],
                "exploratory": [],
            }
            (root / "round_ranking.json").write_text(json.dumps(ranking))
            sys_argv = sys.argv
            try:
                sys.argv = ["summarize_round.py", "--workspace", str(root)]
                self.assertEqual(summarize_round.main(), 0)
            finally:
                sys.argv = sys_argv
            text = (root / "round_results.md").read_text()
            self.assertIn("## Official", text)
            self.assertIn("c1", text)
            self.assertIn("Only the official table", text)


if __name__ == "__main__":
    unittest.main()
