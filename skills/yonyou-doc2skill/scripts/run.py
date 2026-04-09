#!/usr/bin/env python3
"""Run the embedded Yonyou Doc2Skill runtime."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SCRIPT_PREFIX = "[Yonyou Doc2Skill]"
SKILL_ROOT_ENV = "YONYOU_DOC2SKILL_SKILL_ROOT"


def skill_root() -> Path:
    """Return the embedded skill root directory."""
    override = os.environ.get(SKILL_ROOT_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import bootstrap  # noqa: E402


def print_phase(phase: int, message: str) -> None:
    """Print a consistent high-level phase message."""
    print(f"{SCRIPT_PREFIX} Phase {phase}/3: {message}", flush=True)


def _execute_command(argv: list[str]) -> int:
    """Dispatch to the embedded runtime command surface."""
    runtime_root = skill_root() / "runtime"
    embedded_main = runtime_root / "yonyou_doc2skill" / "cli" / "main.py"
    python_executable = bootstrap.python_bin_for_venv(bootstrap.venv_dir())
    if embedded_main.exists() and python_executable.exists():
        env = os.environ.copy()
        existing_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = (
            f"{runtime_root}{os.pathsep}{existing_pythonpath}" if existing_pythonpath else str(runtime_root)
        )
        command = [str(python_executable), "-m", "yonyou_doc2skill.cli.main", *argv]
        return subprocess.run(command, cwd=skill_root(), env=env).returncode

    print(f"{SCRIPT_PREFIX} Error: embedded runtime is not packaged yet", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    """Initialize the runtime on demand and execute the requested command."""
    if argv is None:
        argv = sys.argv[1:]

    if not bootstrap.is_initialized():
        print_phase(1, "Initializing embedded runtime")
        code = bootstrap.main()
        if code != 0:
            return code

    print_phase(2, "Preparing requested command")
    print_phase(3, "Running requested command")
    return _execute_command(argv)


if __name__ == "__main__":
    raise SystemExit(main())
