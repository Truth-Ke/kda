#!/usr/bin/env python3
"""Create a KDA task workspace from the template and install skills."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "templates" / "task-workspace"
INSTALL = REPO_ROOT / "scripts" / "install_skills.py"


def replace_placeholders(root: Path, values: dict[str, str]) -> None:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        original = text
        for key, value in values.items():
            text = text.replace("{{" + key + "}}", value)
        if text != original:
            path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="task workspace path")
    parser.add_argument("--task-name", default="<task>")
    parser.add_argument("--objective", default="<fill in the objective>")
    parser.add_argument("--force", action="store_true", help="copy into a non-empty target")
    args = parser.parse_args()

    target = args.target.resolve()
    if not TEMPLATE.is_dir():
        raise SystemExit(f"template not found: {TEMPLATE}")
    if target.exists() and any(target.iterdir()) and not args.force:
        raise SystemExit(f"target is not empty: {target} (use --force)")
    target.mkdir(parents=True, exist_ok=True)
    shutil.copytree(TEMPLATE, target, dirs_exist_ok=True)
    replace_placeholders(
        target,
        {
            "TASK_NAME": args.task_name,
            "OBJECTIVE": args.objective,
            "DATE": date.today().isoformat(),
            "KDA_ROOT": str(REPO_ROOT),
        },
    )

    result = subprocess.run(
        [sys.executable, str(INSTALL), "--target", str(target)],
        check=False,
    )
    if result.returncode != 0:
        print("skill installation failed", file=sys.stderr)
        return result.returncode
    print(f"created task workspace: {target}")
    print("next: fill contracts/task.yaml, freeze the oracle, then run the baseline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
