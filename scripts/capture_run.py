#!/usr/bin/env python3
"""Run a command and capture an immutable KDA run directory.

Usage:
    python3 scripts/capture_run.py --run-id r001 --code src/kernel.py -- python bench.py
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ENV_KEYS = [
    "PATH",
    "CUDA_HOME",
    "CUDA_VISIBLE_DEVICES",
    "NVIDIA_VISIBLE_DEVICES",
    "LD_LIBRARY_PATH",
    "PYTHONPATH",
    "VIRTUAL_ENV",
    "CONDA_PREFIX",
]


def code_hash(paths: list[Path]) -> str:
    """Hash source content by path relative to each --code root.

    Generated caches and VCS metadata are excluded so a run hash stays stable
    when the same source is copied to a snapshot directory.
    """
    digest = hashlib.sha256()
    ignored_parts = {"__pycache__", ".git", ".mypy_cache", ".pytest_cache"}
    ignored_suffixes = {".pyc", ".pyo"}
    for path in sorted(paths):
        if path.is_dir():
            root = path
            files = sorted(item for item in path.rglob("*") if item.is_file())
        else:
            root = path.parent
            files = [path]
        for item in files:
            if ignored_parts.intersection(item.parts) or item.suffix in ignored_suffixes:
                continue
            digest.update(item.relative_to(root).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(item.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--run-id", help="default: UTC timestamp")
    parser.add_argument("--code", action="append", type=Path, default=[], help="code file or directory to hash")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    command = args.command
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SystemExit("missing command after --")

    workspace = args.workspace.resolve()
    run_id = args.run_id or datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")
    run_dir = workspace / "runs" / run_id
    if run_dir.exists() and not args.force:
        raise SystemExit(f"run directory exists: {run_dir} (use --force)")
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "command.txt").write_text(" ".join(command) + "\n", encoding="utf-8")
    env = {key: os.environ[key] for key in ENV_KEYS if key in os.environ}
    (run_dir / "env.json").write_text(
        json.dumps(
            {
                "cwd": str(workspace),
                "env": env,
                "python": sys.version,
                "platform": sys.platform,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    if args.code:
        code_paths = [
            path if path.is_absolute() else (workspace / path)
            for path in args.code
        ]
        (run_dir / "code_hash.txt").write_text(code_hash(code_paths) + "\n", encoding="utf-8")

    start = time.monotonic()
    started_at = datetime.now(timezone.utc).isoformat()
    with (run_dir / "stdout.log").open("w", encoding="utf-8") as stdout, (
        run_dir / "stderr.log"
    ).open("w", encoding="utf-8") as stderr:
        result = subprocess.run(command, cwd=workspace, stdout=stdout, stderr=stderr)
    duration = time.monotonic() - start

    (run_dir / "result.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "exit_code": result.returncode,
                "started_at": started_at,
                "duration_s": duration,
                "command": command,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "agent_trace.jsonl").touch()
    (run_dir / "usage.json").write_text(
        json.dumps(
            {
                "wall_clock_s": duration,
                "gpu_time_s": None,
                "tokens_in": None,
                "tokens_out": None,
                "cost_usd": None,
                "hardware": "record separately in env.json or task notes",
                "notes": "captured automatically; fill GPU/token/cost fields when known",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"run {run_id}: exit={result.returncode} duration={duration:.2f}s -> {run_dir}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
