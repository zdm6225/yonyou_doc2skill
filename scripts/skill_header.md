---
name: yonyou-doc2skill
description: Generate LLM skills from documentation, codebases, and GitHub repositories
---

# Yonyou Doc2Skill

## Prerequisites

```bash
pip install yonyou-doc2skill
# Or: uv pip install yonyou-doc2skill
```

## Commands

| Source | Command |
|--------|---------|
| Local code | `yonyou-doc2skill create ./path` |
| Docs URL | `yonyou-doc2skill create https://docs.example.com` |
| GitHub | `yonyou-doc2skill create owner/repo` |
| PDF | `yonyou-doc2skill create document.pdf` |

## Quick Start

```bash
# Analyze local codebase
yonyou-doc2skill create /path/to/project --name my-skill

# Package for Claude
yes | yonyou-doc2skill package output/my-skill/ --no-open
```

## Options

| Flag | Description |
|------|-------------|
| `--depth surface/deep/full` | Analysis depth |
| `--skip-patterns` | Skip pattern detection |
| `--skip-test-examples` | Skip test extraction |
| `--ai-mode none/api/local` | AI enhancement |

---

