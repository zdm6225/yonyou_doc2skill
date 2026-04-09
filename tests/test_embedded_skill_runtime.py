"""Tests for the embedded skill runtime scripts."""

import builtins
import importlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest


def load_script_module(script_path: Path, module_name: str):
    """Load a script file as an isolated module."""
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def repo_skill_dir():
    """Return the checked-in skill directory."""
    return Path(__file__).parent.parent / "skills" / "yonyou-doc2skill"


def test_bootstrap_creates_runtime_marker(tmp_path, monkeypatch, repo_skill_dir):
    """Bootstrap should create the runtime marker after initialization."""
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "requirements.txt").write_text("requests\n")
    runtime_dir = skill_dir / "runtime" / "yonyou_doc2skill"
    runtime_dir.mkdir(parents=True)
    (runtime_dir / "__init__.py").write_text("__version__ = '0.0.0'\n", encoding="utf-8")

    bootstrap = load_script_module(repo_skill_dir / "scripts" / "bootstrap.py", "embedded_bootstrap")

    monkeypatch.setenv("YONYOU_DOC2SKILL_SKILL_ROOT", str(skill_dir))
    monkeypatch.setattr(bootstrap, "create_virtualenv", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(bootstrap, "install_dependencies", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(bootstrap, "verify_runtime", lambda *_args, **_kwargs: None)

    result = bootstrap.main()

    assert result == 0
    marker = skill_dir / ".runtime" / "initialized.json"
    assert marker.exists()
    payload = json.loads(marker.read_text())
    assert payload["initialized"] is True
    assert payload["requirements_hash"]


def test_embedded_runtime_includes_profile_modules(repo_skill_dir):
    """Embedded runtime should include profile-aware generation dependencies."""
    runtime_cli = repo_skill_dir / "runtime" / "yonyou_doc2skill" / "cli"

    assert (runtime_cli / "profile_detection.py").exists()
    assert (runtime_cli / "profile_templates.py").exists()


def test_embedded_runtime_create_arguments_export_profile_choices(repo_skill_dir):
    """Embedded runtime create arguments should expose skill profile choices."""
    runtime_root = repo_skill_dir / "runtime"
    sys.path.insert(0, str(runtime_root))
    try:
        create_args = importlib.import_module("yonyou_doc2skill.cli.arguments.create")
    finally:
        sys.path.remove(str(runtime_root))

    assert hasattr(create_args, "SKILL_PROFILE_CHOICES")
    assert "reference" in create_args.SKILL_PROFILE_CHOICES


def test_embedded_runtime_create_command_passes_profile_to_web_config(repo_skill_dir):
    """Embedded runtime create command should preserve profile for web sources."""
    create_command = load_script_module(
        repo_skill_dir / "runtime" / "yonyou_doc2skill" / "cli" / "create_command.py",
        "embedded_runtime_create_command",
    )

    command = create_command.CreateCommand.__new__(create_command.CreateCommand)
    command.args = type(
        "Args",
        (),
        {
            "description": None,
            "skill_profile": None,
            "profile": "reference",
            "config": None,
        },
    )()
    command.source_info = type(
        "SourceInfo",
        (),
        {
            "type": "web",
            "parsed": {"url": "https://react.dev"},
            "raw_input": "https://react.dev",
            "suggested_name": "react-docs",
        },
    )()

    ctx = type(
        "Ctx",
        (),
        {
            "output": type("Output", (), {"name": None, "doc_version": None})(),
            "scraping": type(
                "Scraping",
                (),
                {
                    "max_pages": 50,
                    "rate_limit": 0,
                    "browser": False,
                    "browser_wait_until": "domcontentloaded",
                    "browser_extra_wait": 0,
                    "workers": 1,
                    "async_mode": False,
                    "resume": False,
                    "fresh": False,
                    "skip_scrape": False,
                },
            )(),
        },
    )()

    config = command._build_config("web", ctx)
    assert config["skill_profile"] == "reference"


def test_run_script_skips_bootstrap_after_initialization(tmp_path, monkeypatch, repo_skill_dir, capsys):
    """A pre-initialized runtime should skip bootstrap and dispatch directly."""
    skill_dir = tmp_path / "skill"
    runtime_dir = skill_dir / ".runtime"
    runtime_dir.mkdir(parents=True)
    embedded_python = skill_dir / ".runtime" / ".venv" / "bin" / "python"
    embedded_python.parent.mkdir(parents=True)
    embedded_python.write_text("", encoding="utf-8")

    requirements = skill_dir / "requirements.txt"
    requirements.write_text("requests\n", encoding="utf-8")

    runtime_src = skill_dir / "runtime" / "yonyou_doc2skill" / "cli"
    runtime_src.mkdir(parents=True)
    (runtime_src / "main.py").write_text("print('ok')", encoding="utf-8")

    bootstrap = load_script_module(repo_skill_dir / "scripts" / "bootstrap.py", "embedded_bootstrap_skip")
    run = load_script_module(repo_skill_dir / "scripts" / "run.py", "embedded_run_skip")

    monkeypatch.setenv("YONYOU_DOC2SKILL_SKILL_ROOT", str(skill_dir))
    (runtime_dir / "initialized.json").write_text(
        json.dumps(
            {
                "initialized": True,
                "python": str(embedded_python),
                "requirements": str(requirements),
                "requirements_hash": bootstrap.requirements_hash(),
            }
        )
    )

    called = {"bootstrap": False, "command": None}

    def fail_bootstrap(*_args, **_kwargs):
        called["bootstrap"] = True
        raise AssertionError("bootstrap should not run when initialized")

    class Completed:
        returncode = 0

    def fake_run(command, cwd=None, env=None):
        called["command"] = {"command": command, "cwd": cwd, "env": env}
        return Completed()

    monkeypatch.setattr(bootstrap, "main", fail_bootstrap)
    monkeypatch.setattr(run, "bootstrap", bootstrap)
    monkeypatch.setattr(bootstrap, "venv_dir", lambda: skill_dir / ".runtime" / ".venv")
    monkeypatch.setattr(bootstrap, "python_bin_for_venv", lambda _path: embedded_python)
    monkeypatch.setattr(run.subprocess, "run", fake_run)

    result = run.main(["create", "input", "--name", "demo"])

    captured = capsys.readouterr()
    assert result == 0
    assert called["bootstrap"] is False
    assert called["command"]["command"] == [
        str(embedded_python),
        "-m",
        "yonyou_doc2skill.cli.main",
        "create",
        "input",
        "--name",
        "demo",
    ]
    assert "Step 1/6" not in captured.out
    assert "Phase 1/3" not in captured.out
    assert "Phase 3/3: Running requested command" in captured.out


def test_stale_marker_triggers_rebootstrap(tmp_path, monkeypatch, repo_skill_dir):
    """A missing embedded python should force bootstrap even if the marker exists."""
    skill_dir = tmp_path / "skill"
    runtime_dir = skill_dir / ".runtime"
    runtime_dir.mkdir(parents=True)
    (skill_dir / "requirements.txt").write_text("requests\n", encoding="utf-8")
    runtime_src = skill_dir / "runtime" / "yonyou_doc2skill" / "cli"
    runtime_src.mkdir(parents=True)
    (runtime_src / "main.py").write_text("print('ok')", encoding="utf-8")

    bootstrap = load_script_module(repo_skill_dir / "scripts" / "bootstrap.py", "embedded_bootstrap_stale")
    run = load_script_module(repo_skill_dir / "scripts" / "run.py", "embedded_run_stale")
    monkeypatch.setenv("YONYOU_DOC2SKILL_SKILL_ROOT", str(skill_dir))

    missing_python = skill_dir / ".runtime" / ".venv" / "bin" / "python"
    (runtime_dir / "initialized.json").write_text(
        json.dumps(
            {
                "initialized": True,
                "python": str(missing_python),
                "requirements": str(skill_dir / "requirements.txt"),
                "requirements_hash": bootstrap.requirements_hash(),
            }
        )
    )

    called = {"bootstrap": False}

    def fake_bootstrap_main():
        called["bootstrap"] = True
        return 0

    monkeypatch.setattr(bootstrap, "main", fake_bootstrap_main)
    monkeypatch.setattr(run, "bootstrap", bootstrap)
    monkeypatch.setattr(run, "_execute_command", lambda argv: 0)

    result = run.main(["create", "input", "--name", "demo"])

    assert result == 0
    assert called["bootstrap"] is True


def test_run_script_reports_ordered_phases_during_first_run(
    tmp_path, monkeypatch, repo_skill_dir, capsys
):
    """First run should report initialization before command execution."""
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "requirements.txt").write_text("requests\n", encoding="utf-8")
    runtime_src = skill_dir / "runtime" / "yonyou_doc2skill" / "cli"
    runtime_src.mkdir(parents=True)
    (runtime_src / "main.py").write_text("print('ok')", encoding="utf-8")

    bootstrap = load_script_module(repo_skill_dir / "scripts" / "bootstrap.py", "embedded_bootstrap_order")
    run = load_script_module(repo_skill_dir / "scripts" / "run.py", "embedded_run_order")

    monkeypatch.setenv("YONYOU_DOC2SKILL_SKILL_ROOT", str(skill_dir))
    monkeypatch.setattr(bootstrap, "is_initialized", lambda: False)
    monkeypatch.setattr(run, "bootstrap", bootstrap)
    monkeypatch.setattr(bootstrap, "main", lambda: 0)
    monkeypatch.setattr(run, "_execute_command", lambda _argv: 0)

    result = run.main(["create", "input", "--name", "demo"])

    captured = capsys.readouterr()
    assert result == 0
    assert "Phase 1/3: Initializing embedded runtime" in captured.out
    assert "Phase 2/3: Preparing requested command" in captured.out
    assert "Phase 3/3: Running requested command" in captured.out
    assert captured.out.index("Phase 1/3") < captured.out.index("Phase 2/3")
    assert captured.out.index("Phase 2/3") < captured.out.index("Phase 3/3")


def test_run_script_phase_output_flushes_immediately(monkeypatch, repo_skill_dir):
    """High-level phase logs should flush immediately for agent runners."""
    run = load_script_module(repo_skill_dir / "scripts" / "run.py", "embedded_run_flush")

    calls = []

    def fake_print(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(builtins, "print", fake_print)

    run.print_phase(2, "Preparing requested command")

    assert calls
    assert calls[0][0] == ("[Yonyou Doc2Skill] Phase 2/3: Preparing requested command",)
    assert calls[0][1]["flush"] is True


def test_bootstrap_step_output_flushes_immediately(monkeypatch, repo_skill_dir):
    """Bootstrap step logs should flush immediately for long-running setup."""
    bootstrap = load_script_module(
        repo_skill_dir / "scripts" / "bootstrap.py", "embedded_bootstrap_flush"
    )

    calls = []

    def fake_print(*args, **kwargs):
        calls.append((args, kwargs))

    monkeypatch.setattr(builtins, "print", fake_print)

    bootstrap.print_step(3, "Installing dependencies")

    assert calls
    assert calls[0][0] == ("[Yonyou Doc2Skill] Step 3/6: Installing dependencies",)
    assert calls[0][1]["flush"] is True


def test_install_dependencies_writes_quiet_log_file(tmp_path, monkeypatch, repo_skill_dir, capsys):
    """Dependency installation should keep terminal output concise and log details to disk."""
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "requirements.txt").write_text("requests==1.0.0\n", encoding="utf-8")
    bootstrap = load_script_module(repo_skill_dir / "scripts" / "bootstrap.py", "embedded_bootstrap_quiet")
    monkeypatch.setenv("YONYOU_DOC2SKILL_SKILL_ROOT", str(skill_dir))

    captured_run = {}

    class Completed:
        stdout = "Collecting requests\nSuccessfully installed requests"
        stderr = "pip warning"

    def fake_run(command, check, stdout, stderr, text):
        captured_run["command"] = command
        captured_run["stdout"] = stdout
        captured_run["stderr"] = stderr
        captured_run["text"] = text
        return Completed()

    monkeypatch.setattr(bootstrap.subprocess, "run", fake_run)

    bootstrap.install_dependencies(Path("/tmp/python"), skill_dir / "requirements.txt")

    out = capsys.readouterr().out
    assert captured_run["stdout"] == bootstrap.subprocess.PIPE
    assert captured_run["stderr"] == bootstrap.subprocess.STDOUT
    assert captured_run["text"] is True
    assert "Collecting requests" not in out
    assert "Dependency installation started" in out
    assert "Dependency installation finished" in out
    assert "Detailed dependency logs:" in out
    install_log = skill_dir / ".runtime" / "logs" / "pip-install.log"
    assert install_log.exists()
    assert "Successfully installed requests" in install_log.read_text(encoding="utf-8")


def test_run_script_passes_profile_argument_through(tmp_path, monkeypatch, repo_skill_dir):
    """Profile arguments should be passed through to the embedded runtime unchanged."""
    skill_dir = tmp_path / "skill"
    runtime_dir = skill_dir / ".runtime"
    runtime_dir.mkdir(parents=True)
    embedded_python = skill_dir / ".runtime" / ".venv" / "bin" / "python"
    embedded_python.parent.mkdir(parents=True)
    embedded_python.write_text("", encoding="utf-8")
    requirements = skill_dir / "requirements.txt"
    requirements.write_text("requests\n", encoding="utf-8")
    runtime_src = skill_dir / "runtime" / "yonyou_doc2skill" / "cli"
    runtime_src.mkdir(parents=True)
    (runtime_src / "main.py").write_text("print('ok')", encoding="utf-8")

    bootstrap = load_script_module(repo_skill_dir / "scripts" / "bootstrap.py", "embedded_bootstrap_profile")
    run = load_script_module(repo_skill_dir / "scripts" / "run.py", "embedded_run_profile")

    monkeypatch.setenv("YONYOU_DOC2SKILL_SKILL_ROOT", str(skill_dir))
    (runtime_dir / "initialized.json").write_text(
        json.dumps(
            {
                "initialized": True,
                "python": str(embedded_python),
                "requirements": str(requirements),
                "requirements_hash": bootstrap.requirements_hash(),
            }
        )
    )

    captured = {}

    class Completed:
        returncode = 0

    def fake_run(command, cwd=None, env=None):
        captured["command"] = command
        return Completed()

    monkeypatch.setattr(run, "bootstrap", bootstrap)
    monkeypatch.setattr(bootstrap, "venv_dir", lambda: skill_dir / ".runtime" / ".venv")
    monkeypatch.setattr(bootstrap, "python_bin_for_venv", lambda _path: embedded_python)
    monkeypatch.setattr(run.subprocess, "run", fake_run)

    result = run.main(["create", "https://react.dev", "--profile", "reference", "--name", "react"])

    assert result == 0
    assert captured["command"] == [
        str(embedded_python),
        "-m",
        "yonyou_doc2skill.cli.main",
        "create",
        "https://react.dev",
        "--profile",
        "reference",
        "--name",
        "react",
    ]
