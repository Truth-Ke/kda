#!/usr/bin/env python3
"""Install vendored KDA skills into a workspace's .claude/skills directory.

The canonical copies live under this repository's ``skills/`` tree. Claude
Code discovers project skills from ``.claude/skills/``, so a task workspace
needs links (or copies) there. This script is intentionally small: scan,
parse the frontmatter name, link, and write a lock file.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPO_ROOT / "skills"


def frontmatter_name(skill_file: Path) -> str | None:
    text = skill_file.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    block = text[3:end]
    match = re.search(r"^name:\s*[\"']?([^\"'\n]+)", block, re.MULTILINE)
    return match.group(1).strip() if match else None


def source_license(skill_dir: Path) -> str:
    source = skill_dir / "SOURCE.yaml"
    if not source.exists():
        return "unknown"
    text = source.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"^license:\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else "unknown"


def discover(source_root: Path) -> list[tuple[str, Path]]:
    found: dict[str, Path] = {}
    for skill_file in sorted(source_root.rglob("SKILL.md")):
        name = frontmatter_name(skill_file)
        if not name:
            print(f"warning: no frontmatter name in {skill_file}", file=sys.stderr)
            continue
        if name in found:
            print(
                f"warning: duplicate skill name {name!r}: {found[name]} and "
                f"{skill_file.parent}",
                file=sys.stderr,
            )
            continue
        found[name] = skill_file.parent
    return sorted(found.items())


def install_one(
    name: str,
    skill_dir: Path,
    target: Path,
    copy: bool,
    force: bool,
) -> Path:
    destination = target / ".claude" / "skills" / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_symlink() or destination.is_file():
        destination.unlink()
    elif destination.is_dir():
        if not force:
            raise SystemExit(
                f"refusing to replace non-symlink {destination}; use --force"
            )
        shutil.rmtree(destination)
    if copy:
        shutil.copytree(skill_dir, destination)
    else:
        os.symlink(skill_dir.resolve(), destination, target_is_directory=True)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="vendored skills root (default: <repo>/skills)",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=Path.cwd(),
        help="workspace to install into (default: current directory)",
    )
    parser.add_argument("--copy", action="store_true", help="copy instead of symlink")
    parser.add_argument("--force", action="store_true", help="replace existing directories")
    parser.add_argument("--only", help="comma-separated skill names")
    parser.add_argument("--list", action="store_true", help="list discovered skills")
    args = parser.parse_args()

    source_root = args.source.resolve()
    target = args.target.resolve()
    if not source_root.is_dir():
        raise SystemExit(f"skills root not found: {source_root}")

    skills = discover(source_root)
    if args.only:
        wanted = {item.strip() for item in args.only.split(",") if item.strip()}
        skills = [(name, path) for name, path in skills if name in wanted]
        missing = wanted - {name for name, _ in skills}
        if missing:
            raise SystemExit(f"skills not found: {', '.join(sorted(missing))}")

    if args.list:
        for name, path in skills:
            print(f"{name}\t{path}")
        return 0

    installed = []
    for name, skill_dir in skills:
        try:
            destination = install_one(name, skill_dir, target, args.copy, args.force)
        except SystemExit as exc:
            print(str(exc), file=sys.stderr)
            continue
        installed.append(
            {
                "name": name,
                "source": str(skill_dir),
                "target": str(destination),
                "license": source_license(skill_dir),
                "installed_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        print(f"installed {name} -> {destination}")

    lock = target / "skills.lock.json"
    lock.write_text(json.dumps({"skills": installed}, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {lock}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
