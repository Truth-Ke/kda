# Copyright 2026 Co-developed by KDA (Kernel Design Agents)

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts import capture_run  # noqa: E402


class CaptureRunTests(unittest.TestCase):
    def test_hash_is_stable_across_cache_and_snapshot_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src"
            snapshot = root / "artifacts" / "c1" / "hash"
            source.mkdir()
            (source / "kernel.py").write_text("def run(): return 1\n")
            (source / "__pycache__").mkdir()
            (source / "__pycache__" / "kernel.pyc").write_bytes(b"cache")
            shutil.copytree(source, snapshot, ignore=shutil.ignore_patterns("__pycache__"))
            self.assertEqual(
                capture_run.code_hash([source]),
                capture_run.code_hash([snapshot]),
            )


if __name__ == "__main__":
    unittest.main()
