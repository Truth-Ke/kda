# Copyright 2026 Co-developed by KDA (Kernel Design Agents)

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts import install_skills  # noqa: E402


class InstallSkillsTests(unittest.TestCase):
    def test_discovers_and_links_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "skills" / "behavior" / "demo"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text(
                "---\nname: demo\ndescription: demo skill\n---\n\n# Demo\n"
            )
            (source / "SOURCE.yaml").write_text("license: MIT\n")
            target = root / "workspace"
            target.mkdir()

            discovered = install_skills.discover(root / "skills")
            self.assertEqual([name for name, _ in discovered], ["demo"])
            destination = install_skills.install_one(
                "demo", source, target, copy=False, force=False
            )
            self.assertTrue(destination.is_symlink())
            self.assertTrue((destination / "SKILL.md").exists())

    def test_copy_force_replaces_existing_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "skills" / "demo"
            source.mkdir(parents=True)
            (source / "SKILL.md").write_text(
                "---\nname: demo\ndescription: demo skill\n---\n\n# Demo\n"
            )
            target = root / "workspace"
            destination = target / ".claude" / "skills" / "demo"
            destination.mkdir(parents=True)
            (destination / "old.txt").write_text("old")
            install_skills.install_one(
                "demo", source, target, copy=True, force=True
            )
            self.assertFalse((destination / "old.txt").exists())
            self.assertTrue((destination / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
