---
title: Embedded Runtime Skill Design For Yonyou Doc2Skill
date: 2026-04-08
status: draft
---

# Goal

Turn the published `Yonyou Doc2Skill` skill into a self-contained skill package that can bootstrap and run its own local execution environment on first use.

The target user experience is:
- install the skill package
- invoke the skill from the agent
- the first run prepares the runtime automatically
- later runs directly execute the requested `create`, `confluence`, or `package` flow

The current standalone CLI must remain available for direct local use.

# Recommendation

Use a dual-entry architecture with one shared core:

- keep `yonyou-doc2skill` CLI for developers and direct terminal use
- add an embedded runtime inside the published skill package
- add small skill-local scripts that bootstrap and invoke the embedded runtime
- avoid maintaining two independent implementations of the generation logic

This keeps the current CLI intact while making the published skill usable without requiring a separate manual CLI installation step.

# Published Skill Package Shape

The published package should become:

```text
skills/yonyou-doc2skill/
  SKILL.md
  package.json
  requirements.txt
  scripts/
    bootstrap.py
    run.py
  runtime/
    yonyou_doc2skill/
      ...
```

Purpose of each part:

- `SKILL.md`
  Agent-facing instructions. It should call the local skill scripts rather than the global `yonyou-doc2skill` command.

- `package.json`
  Skill marketplace metadata.

- `requirements.txt`
  Python dependencies required by the embedded runtime.

- `scripts/bootstrap.py`
  First-run initializer. It prepares a skill-private Python environment.

- `scripts/run.py`
  Runtime entrypoint called by the skill. It ensures bootstrap has completed, then dispatches to the embedded execution flow.

- `runtime/yonyou_doc2skill/`
  Embedded Python runtime code that provides the actual generation behavior.

# Runtime Model

## Direct CLI path

The existing terminal workflow remains unchanged:

- `yonyou-doc2skill create ...`
- `yonyou-doc2skill confluence ...`
- `yonyou-doc2skill package ...`

This path remains the preferred path for development, debugging, and direct batch usage.

## Skill path

The published skill executes through local scripts:

1. Agent loads the skill.
2. The skill invokes `python3 scripts/run.py ...`.
3. `run.py` checks whether the skill runtime is initialized.
4. If not initialized, `run.py` invokes `bootstrap.py`.
5. `bootstrap.py` creates a private `.venv`, installs dependencies, validates the runtime, and writes an initialization marker.
6. `run.py` continues with the requested operation using the embedded runtime.

# Initialization Behavior

First use is expected to be slower. The skill must show clear progress output so the user can tell the difference between initialization and generation.

Required bootstrap output shape:

```text
[Yonyou Doc2Skill] Step 1/6: Checking Python runtime
[Yonyou Doc2Skill] Step 2/6: Preparing local environment
[Yonyou Doc2Skill] Step 3/6: Installing dependencies
[Yonyou Doc2Skill] Step 4/6: Verifying runtime
[Yonyou Doc2Skill] Step 5/6: Preparing requested command
[Yonyou Doc2Skill] Step 6/6: Running generation
```

Initialization must also emit actionable failures such as:

- Python not found
- unsupported Python version
- dependency installation failed
- network unavailable during dependency installation
- runtime validation failed

# Environment Strategy

The embedded skill uses a skill-private environment instead of a shared global install.

Recommended layout:

```text
skills/yonyou-doc2skill/
  .runtime/
    .venv/
    initialized.json
```

Rules:

- do not require a global `yonyou-doc2skill` install
- do not depend on a shared user-level Python virtual environment
- keep all runtime state inside the installed skill directory
- allow safe re-bootstrap when the marker file is missing or invalid

# Core Reuse Strategy

There should be one shared behavior surface, not two divergent implementations.

Recommended implementation sequence:

1. Keep the existing CLI intact.
2. Introduce a small shared runtime surface for command dispatch and initialization-safe execution.
3. Make the embedded skill scripts call that shared runtime surface.
4. Leave the current CLI commands wired to the same underlying behavior.

The first implementation phase does not need to fully refactor the entire codebase into a clean `core/` package. It is acceptable to add a thin compatibility layer first, then move deeper shared logic later.

# SKILL.md Changes

The official skill should stop assuming that `yonyou-doc2skill` is globally installed.

Instead it should:

- call `scripts/run.py`
- explain that the first run may initialize the runtime
- mention that initialization progress will be printed
- continue to describe retained source types only

The skill should still present the same product promise:
- generate skills from supported sources
- report output paths
- optionally package the generated skill

# Compatibility Boundaries

The embedded runtime should preserve the public product surface:

- `create`
- `confluence`
- `package`

Other commands can remain CLI-only during the first phase if needed. The embedded skill only needs to support the user-facing generation path required for marketplace distribution.

# Risks

- skill marketplaces may differ in whether they preserve executable helper files exactly as packaged
- some user environments may not permit dependency installation during first run
- first-run latency may feel high without explicit progress output
- embedding the runtime increases the published package size
- optional dependencies may need staged installation or selective inclusion

# Phase Recommendation

Implement in two phases.

## Phase 1

Minimum viable embedded runtime:

- add `scripts/bootstrap.py`
- add `scripts/run.py`
- add `requirements.txt`
- update `SKILL.md` to use the local scripts
- support first-run initialization messages
- keep the existing CLI untouched

## Phase 2

Deep cleanup and hardening:

- reduce duplicated packaging logic
- tighten dependency groups for embedded use
- improve re-bootstrap and repair flows
- consider narrowing the embedded command surface further if marketplace execution constraints require it

# Verification

Before implementation is considered complete:

- the published skill directory must include `SKILL.md`, `package.json`, `requirements.txt`, and `scripts/`
- the first embedded run must show initialization progress output
- a second embedded run must skip initialization and execute directly
- the direct CLI path must still work
- failure messages must distinguish bootstrap failures from generation failures
