---
title: Official Yonyou Doc2Skill Wrapper Skill Design
date: 2026-04-07
status: draft
---

# Goal

Create an official `Yonyou Doc2Skill` skill that end users can install into their agent environment and use to generate their own skills through the locally installed `yonyou-doc2skill` CLI.

# Recommendation

Use a local wrapper skill.

The skill will:
- explain what source types are supported
- collect the minimum required inputs from the user
- choose the right `yonyou-doc2skill` command path
- instruct the agent to run the local CLI
- explain expected outputs and next steps

The skill will not:
- embed scraper logic itself
- replace the CLI
- depend on a hosted backend

# User Experience

## Installation

End users install:
- the `yonyou-doc2skill` package locally
- the official skill directory into their agent's skills folder

## Runtime flow

1. User asks the agent to create a skill from a source.
2. The official skill identifies the source type and desired output name.
3. The skill directs the agent to run local `yonyou-doc2skill create ...`.
4. If requested, the skill follows with `yonyou-doc2skill package ...`.
5. The user receives the generated output directory or packaged artifact path.

# Skill Content

The official skill should contain:
- a concise description of supported source types
- prerequisites: local install, filesystem access, optional credentials
- a source routing section
- canonical command templates
- output expectations
- troubleshooting notes for common failures

It should avoid:
- internal architecture details
- large product marketing sections
- historical project references

# Packaging Shape

Recommended deliverable:
- `skills/yonyou-doc2skill/SKILL.md`

Optional later additions:
- `examples/` references for common source types
- short install instructions in the root README

# Constraints

- Keep the official skill aligned with the currently supported public source set.
- Do not mention removed source types as available.
- Prefer `yonyou-doc2skill create ...` as the primary user path.
- Treat `package` as optional follow-up, not mandatory.

# Verification

Before considering the wrapper skill complete:
- the skill file must reference `yonyou-doc2skill`, not old names
- the skill instructions must only describe retained source types
- a smoke flow using the installed skill guidance must map cleanly to a working local CLI command

