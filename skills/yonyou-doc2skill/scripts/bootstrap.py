#!/usr/bin/env python3
"""Bootstrap the embedded Yonyou Doc2Skill runtime."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import venv
from hashlib import sha256
from pathlib import Path

SCRIPT_PREFIX = "[Yonyou Doc2Skill]"
SKILL_ROOT_ENV = "YONYOU_DOC2SKILL_SKILL_ROOT"
MIN_PYTHON = (3, 10)


def skill_root() -> Path:
    """Return the embedded skill root directory."""
    override = os.environ.get(SKILL_ROOT_ENV)
    if override:
        return Path(override).expanduser().resolve()
    return Path(__file__).resolve().parents[1]


def runtime_dir() -> Path:
    """Return the private runtime directory for the skill."""
    return skill_root() / ".runtime"


def venv_dir() -> Path:
    """Return the embedded virtual environment directory."""
    return runtime_dir() / ".venv"


def initialized_marker() -> Path:
    """Return the runtime initialization marker path."""
    return runtime_dir() / "initialized.json"


def requirements_file() -> Path:
    """Return the embedded runtime requirements file."""
    return skill_root() / "requirements.txt"


def runtime_source_dir() -> Path:
    """Return the packaged embedded runtime root."""
    return skill_root() / "runtime"


def requirements_hash() -> str:
    """Return a stable digest for the embedded requirements file."""
    return sha256(requirements_file().read_bytes()).hexdigest()


def print_step(step: int, message: str) -> None:
    """Print a consistent progress message."""
    print(f"{SCRIPT_PREFIX} Step {step}/6: {message}", flush=True)


def logs_dir() -> Path:
    """Return the embedded runtime log directory."""
    return runtime_dir() / "logs"


def python_bin_for_venv(path: Path) -> Path:
    """Return the python executable inside a virtual environment."""
    if os.name == "nt":
        return path / "Scripts" / "python.exe"
    return path / "bin" / "python"


def create_virtualenv(target_dir: Path, python_executable: str) -> None:
    """Create the embedded virtual environment."""
    del python_executable
    venv.create(str(target_dir), with_pip=True, clear=False)


def install_dependencies(python_executable: Path, requirements: Path) -> None:
    """Install the runtime dependencies into the embedded virtualenv."""
    logs_dir().mkdir(parents=True, exist_ok=True)
    install_log = logs_dir() / "pip-install.log"
    print(f"{SCRIPT_PREFIX} Dependency installation started", flush=True)
    print(f"{SCRIPT_PREFIX} Detailed dependency logs: {install_log}", flush=True)

    completed = subprocess.run(
        [str(python_executable), "-m", "pip", "install", "-r", str(requirements)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    install_log.write_text(completed.stdout or "", encoding="utf-8")
    print(f"{SCRIPT_PREFIX} Dependency installation finished", flush=True)


def verify_runtime(python_executable: Path) -> None:
    """Verify the embedded runtime imports the required core dependencies."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(runtime_source_dir())
    subprocess.run(
        [
            str(python_executable),
            "-c",
            (
                "import requests, bs4, yaml, pydantic; "
                "from yonyou_doc2skill.cli.main import create_parser; "
                "create_parser()"
            ),
        ],
        check=True,
        env=env,
    )


def write_initialized_marker(python_executable: Path) -> None:
    """Persist the runtime initialization marker."""
    runtime_dir().mkdir(parents=True, exist_ok=True)
    payload = {
        "initialized": True,
        "python": str(python_executable),
        "requirements": str(requirements_file()),
        "requirements_hash": requirements_hash(),
    }
    initialized_marker().write_text(json.dumps(payload, indent=2, sort_keys=True))


def is_initialized() -> bool:
    """Return True when the embedded runtime already exists."""
    marker = initialized_marker()
    if not marker.exists():
        return False
    try:
        payload = json.loads(marker.read_text())
    except json.JSONDecodeError:
        return False
    python_executable = Path(payload.get("python", ""))
    return (
        bool(payload.get("initialized"))
        and payload.get("requirements_hash") == requirements_hash()
        and python_executable.exists()
        and (runtime_source_dir() / "yonyou_doc2skill" / "cli" / "main.py").exists()
    )


def main() -> int:
    """Initialize the embedded runtime if necessary."""
    print_step(1, "Checking Python runtime")

    if sys.version_info < MIN_PYTHON:
        print(
            f"{SCRIPT_PREFIX} Error: Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required",
            file=sys.stderr,
        )
        return 1

    python_executable = sys.executable

    print_step(2, "Preparing local environment")
    runtime_dir().mkdir(parents=True, exist_ok=True)
    if not runtime_source_dir().exists():
        print(f"{SCRIPT_PREFIX} Error: embedded runtime not found", file=sys.stderr)
        return 1
    create_virtualenv(venv_dir(), python_executable)

    embedded_python = python_bin_for_venv(venv_dir())

    print_step(3, "Installing dependencies")
    try:
        install_dependencies(embedded_python, requirements_file())
    except subprocess.CalledProcessError as exc:
        install_log = logs_dir() / "pip-install.log"
        if exc.stdout is not None:
            logs_dir().mkdir(parents=True, exist_ok=True)
            install_log.write_text(str(exc.stdout), encoding="utf-8")
        print(
            f"{SCRIPT_PREFIX} Error: dependency installation failed. See {install_log}",
            file=sys.stderr,
        )
        return 1

    print_step(4, "Verifying runtime")
    verify_runtime(embedded_python)

    write_initialized_marker(embedded_python)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
