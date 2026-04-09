# CLI Reference - Yonyou Doc2Skill

> **Version:** 3.4.0
> **Last Updated:** 2026-03-21
> **Complete reference for all 30+ CLI commands**

---

## Table of Contents

- [Overview](#overview)
  - [Installation](#installation)
  - [Global Flags](#global-flags)
  - [Environment Variables](#environment-variables)
- [Command Reference](#command-reference)
  - [analyze](#analyze) - Analyze local codebase
  - [config](#config) - Configuration wizard
  - [create](#create) - Create skill (auto-detects source)
  - [enhance](#enhance) - AI enhancement (local mode)
  - [enhance-status](#enhance-status) - Monitor enhancement
  - [estimate](#estimate) - Estimate page counts
  - [github](#github) - Scrape GitHub repository
  - [install](#install) - One-command complete workflow
  - [install-agent](#install-agent) - Install to AI agent
  - [multilang](#multilang) - Multi-language docs
  - [package](#package) - Package skill for platform
  - [pdf](#pdf) - Extract from PDF
  - [quality](#quality) - Quality scoring
  - [resume](#resume) - Resume interrupted jobs
  - [scrape](#scrape) - Scrape documentation
  - [stream](#stream) - Stream large files
  - [unified](#unified) - Multi-source scraping
  - [update](#update) - Incremental updates
  - [upload](#upload) - Upload to platform
  - [video](#video) - Extract from video
  - [word](#word) - Extract from Word document
  - [epub](#epub) - Extract from EPUB
  - [jupyter](#jupyter) - Extract from Jupyter Notebook
  - [html](#html) - Extract from local HTML
  - [openapi](#openapi) - Extract from OpenAPI/Swagger spec
  - [asciidoc](#asciidoc) - Extract from AsciiDoc
  - [pptx](#pptx) - Extract from PowerPoint
  - [rss](#rss) - Extract from RSS/Atom feed
  - [manpage](#manpage) - Extract from man page
  - [confluence](#confluence) - Extract from Confluence wiki
  - [notion](#notion) - Extract from Notion pages
  - [chat](#chat) - Extract from Slack/Discord export
  - [workflows](#workflows) - Manage workflow presets
- [Common Workflows](#common-workflows)
- [Exit Codes](#exit-codes)
- [Troubleshooting](#troubleshooting)

---

## Overview

Yonyou Doc2Skill provides a unified CLI for converting 17 source types—documentation, GitHub repositories, PDFs, videos, notebooks, wikis, and more—into AI-ready skills.

### Installation

```bash
# Basic installation
pip install yonyou-doc2skill

# With all platform support
pip install yonyou-doc2skill[all-llms]

# Development setup
pip install -e ".[all-llms,dev]"
```

Verify installation:
```bash
yonyou-doc2skill --version
```

### Global Flags

These flags work with most commands:

| Flag | Description |
|------|-------------|
| `-h, --help` | Show help message and exit |
| `--version` | Show version number and exit |
| `-v, --verbose` | Enable verbose (DEBUG) output |
| `-q, --quiet` | Minimize output (WARNING only) |
| `--dry-run` | Preview without executing |

### Environment Variables

See [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) for complete reference.

**Common variables:**

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Claude AI API access |
| `GOOGLE_API_KEY` | Google Gemini API access |
| `OPENAI_API_KEY` | OpenAI API access |
| `GITHUB_TOKEN` | GitHub API (higher rate limits) |

---

## Command Reference

Commands are organized alphabetically.

---

### analyze

Analyze local codebase and extract code knowledge.

**Purpose:** Deep code analysis with pattern detection, API extraction, and documentation generation.

**Syntax:**
```bash
yonyou-doc2skill analyze --directory DIR [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `--directory DIR` | Yes | Directory to analyze |
| `--output DIR` | No | Output directory (default: output/codebase/) |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| | `--preset` | standard | Analysis preset: quick, standard, comprehensive |
| | `--preset-list` | | Show available presets and exit |
| | `--languages` | auto | Comma-separated languages (Python,JavaScript,C++) |
| | `--file-patterns` | | Comma-separated file patterns |
| | `--enhance-level` | 2 | AI enhancement: 0=off, 1=SKILL.md, 2=+config, 3=full |
| | `--skip-api-reference` | | Skip API docs generation |
| | `--skip-dependency-graph` | | Skip dependency graph |
| | `--skip-patterns` | | Skip pattern detection |
| | `--skip-test-examples` | | Skip test example extraction |
| | `--skip-how-to-guides` | | Skip how-to guide generation |
| | `--skip-config-patterns` | | Skip config pattern extraction |
| | `--skip-docs` | | Skip project docs (README) |
| | `--no-comments` | | Skip comment extraction |
| `-v` | `--verbose` | | Enable verbose logging |

**Examples:**

```bash
# Basic analysis with defaults
yonyou-doc2skill analyze --directory ./my-project

# Quick analysis (1-2 min)
yonyou-doc2skill analyze --directory ./my-project --preset quick

# Comprehensive analysis with all features
yonyou-doc2skill analyze --directory ./my-project --preset comprehensive

# Specific languages only
yonyou-doc2skill analyze --directory ./my-project --languages Python,JavaScript

# Skip heavy features for faster analysis
yonyou-doc2skill analyze --directory ./my-project --skip-dependency-graph --skip-patterns
```

**Exit Codes:**
- `0` - Success
- `1` - Analysis failed

---

### config

Interactive configuration wizard for API keys and settings.

**Purpose:** Setup GitHub tokens, API keys, and preferences.

**Syntax:**
```bash
yonyou-doc2skill config [options]
```

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| | `--github` | Go directly to GitHub token setup |
| | `--api-keys` | Go directly to API keys setup |
| | `--show` | Show current configuration |
| | `--test` | Test connections |

**Examples:**

```bash
# Full configuration wizard
yonyou-doc2skill config

# Quick GitHub setup
yonyou-doc2skill config --github

# View current config
yonyou-doc2skill config --show

# Test all connections
yonyou-doc2skill config --test
```

---

### create

Create skill from any source. Auto-detects source type.

**Purpose:** Universal entry point - handles URLs, GitHub repos, local directories, PDFs, and config files automatically.

**Syntax:**
```bash
yonyou-doc2skill create [source] [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `source` | No | Source URL, repo, path, or config file |

**Source Types (Auto-Detected):**
| Source Pattern | Type | Example |
|----------------|------|---------|
| `https://...` | Documentation | `https://docs.react.dev/` |
| `owner/repo` | GitHub | `facebook/react` |
| `./path` | Local codebase | `./my-project` |
| `*.pdf` | PDF | `manual.pdf` |
| `*.docx` | Word Document | `report.docx` |
| `*.epub` | EPUB | `book.epub` |
| `*.ipynb` | Jupyter Notebook | `analysis.ipynb` |
| `*.html` / `*.htm` | Local HTML | `page.html` |
| `*.yaml` / `*.yml` (OpenAPI) | OpenAPI/Swagger | `api-spec.yaml` |
| `*.adoc` / `*.asciidoc` | AsciiDoc | `guide.adoc` |
| `*.pptx` | PowerPoint | `slides.pptx` |
| `*.rss` / `*.atom` | RSS/Atom Feed | `feed.rss` |
| `*.1`–`*.8` / `*.man` | Man Page | `curl.1` |
| `*.json` | Config file | `config.json` |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| `-n` | `--name` | auto | Skill name |
| `-d` | `--description` | auto | Skill description |
| `-o` | `--output` | auto | Output directory |
| `-p` | `--preset` | | Analysis preset: quick, standard, comprehensive |
| `-c` | `--config` | | Load settings from JSON file |
| | `--enhance-level` | 2 | AI enhancement level (0-3) |
| | `--api-key` | | Anthropic API key |
| | `--enhance-workflow` | | Apply workflow preset (can use multiple) |
| | `--enhance-stage` | | Add inline enhancement stage |
| | `--var` | | Override workflow variable (key=value) |
| | `--workflow-dry-run` | | Preview workflow without executing |
| | `--dry-run` | | Preview without creating |
| | `--chunk-for-rag` | | Enable RAG chunking |
| | `--chunk-tokens` | 512 | Chunk size in tokens |
| | `--chunk-overlap-tokens` | 50 | Chunk overlap in tokens |
| | `--help-web` | | Show web scraping options |
| | `--help-github` | | Show GitHub options |
| | `--help-local` | | Show local analysis options |
| | `--help-pdf` | | Show PDF options |
| | `--help-all` | | Show all 120+ options |

**Examples:**

```bash
# Documentation website
yonyou-doc2skill create https://docs.django.com/

# GitHub repository
yonyou-doc2skill create facebook/react

# Local codebase
yonyou-doc2skill create ./my-project

# PDF file
yonyou-doc2skill create manual.pdf --name product-docs

# With preset
yonyou-doc2skill create https://docs.react.dev/ --preset quick

# With enhancement workflow
yonyou-doc2skill create ./my-project --enhance-workflow security-focus

# Multi-workflow chaining
yonyou-doc2skill create ./my-project \
  --enhance-workflow security-focus \
  --enhance-workflow api-documentation
```

---

### enhance

Enhance SKILL.md using local coding agent (Claude Code).

**Purpose:** AI-powered quality improvement without API costs. Requires Claude Code installed.

**Syntax:**
```bash
yonyou-doc2skill enhance SKILL_DIRECTORY [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `SKILL_DIRECTORY` | Yes | Path to skill directory |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| | `--agent` | claude | Local coding agent to use |
| | `--agent-cmd` | | Override agent command template |
| | `--background` | | Run in background |
| | `--daemon` | | Run as daemon |
| | `--no-force` | | Enable confirmations |
| | `--timeout` | 600 | Timeout in seconds |

**Examples:**

```bash
# Basic enhancement
yonyou-doc2skill enhance output/react/

# Background mode
yonyou-doc2skill enhance output/react/ --background

# With custom timeout
yonyou-doc2skill enhance output/react/ --timeout 1200

# Monitor background enhancement
yonyou-doc2skill enhance-status output/react/ --watch
```

**Requirements:** Claude Code must be installed and authenticated.

---

### enhance-status

Monitor background enhancement processes.

**Purpose:** Check status of enhancement running in background/daemon mode.

**Syntax:**
```bash
yonyou-doc2skill enhance-status SKILL_DIRECTORY [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `SKILL_DIRECTORY` | Yes | Path to skill directory |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| `-w` | `--watch` | | Watch in real-time |
| | `--json` | | JSON output |
| | `--interval` | 5 | Watch interval in seconds |

**Examples:**

```bash
# Check status once
yonyou-doc2skill enhance-status output/react/

# Watch continuously
yonyou-doc2skill enhance-status output/react/ --watch

# JSON output for scripting
yonyou-doc2skill enhance-status output/react/ --json
```

---

### estimate

Estimate page count before scraping.

**Purpose:** Preview how many pages will be scraped without downloading.

**Syntax:**
```bash
yonyou-doc2skill estimate [config] [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `config` | No | Config JSON file path |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| | `--all` | | List all available configs |
| | `--max-discovery` | 1000 | Max pages to discover |

**Examples:**

```bash
# Estimate with config file
yonyou-doc2skill estimate configs/react.json

# Quick estimate (100 pages)
yonyou-doc2skill estimate configs/react.json --max-discovery 100

# List all available presets
yonyou-doc2skill estimate --all
```

---

### github

Scrape GitHub repository and generate skill.

**Purpose:** Extract code, issues, releases, and metadata from GitHub repos.

**Syntax:**
```bash
yonyou-doc2skill github [options]
```

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| | `--repo` | | Repository (owner/repo format) |
| `-c` | `--config` | | Config JSON file |
| | `--token` | | GitHub personal access token |
| `-n` | `--name` | auto | Skill name |
| `-d` | `--description` | auto | Description |
| | `--no-issues` | | Skip GitHub issues |
| | `--no-changelog` | | Skip CHANGELOG |
| | `--no-releases` | | Skip releases |
| | `--max-issues` | 100 | Max issues to fetch |
| | `--scrape-only` | | Only scrape, don't build |
| | `--enhance-level` | 2 | AI enhancement (0-3) |
| | `--api-key` | | Anthropic API key |
| | `--enhance-workflow` | | Apply workflow preset |
| | `--non-interactive` | | CI/CD mode (fail fast) |
| | `--profile` | | GitHub profile from config |

**Examples:**

```bash
# Basic repo analysis
yonyou-doc2skill github --repo facebook/react

# With GitHub token (higher rate limits)
yonyou-doc2skill github --repo facebook/react --token $GITHUB_TOKEN

# Skip issues for faster scraping
yonyou-doc2skill github --repo facebook/react --no-issues

# Scrape only, build later
yonyou-doc2skill github --repo facebook/react --scrape-only
```

---

### install

One-command complete workflow: fetch → scrape → enhance → package → upload.

**Purpose:** End-to-end automation for common workflows.

**Syntax:**
```bash
yonyou-doc2skill install --config CONFIG [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `--config CONFIG` | Yes | Config name or path |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| | `--destination` | output/ | Output directory |
| | `--no-upload` | | Skip upload to Claude |
| | `--unlimited` | | Remove page limits |
| | `--dry-run` | | Preview without executing |

**Examples:**

```bash
# Complete workflow with preset
yonyou-doc2skill install --config react

# Skip upload
yonyou-doc2skill install --config react --no-upload

# Custom config
yonyou-doc2skill install --config configs/my-project.json

# Dry run to preview
yonyou-doc2skill install --config react --dry-run
```

**Note:** AI enhancement is mandatory for install command.

---

### install-agent

Install skill to AI agent directories (Cursor, Windsurf, Cline, Roo, Aider, Bolt, Kilo, Continue, Kimi Code).

**Purpose:** Direct installation to IDE AI assistant context directories.

**Syntax:**
```bash
yonyou-doc2skill install-agent SKILL_DIRECTORY --agent AGENT [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `SKILL_DIRECTORY` | Yes | Path to skill directory |
| `--agent AGENT` | Yes | Target agent: cursor, windsurf, cline, continue, roo, aider, bolt, kilo, kimi-code |

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| | `--force` | Overwrite existing |

**Examples:**

```bash
# Install to Cursor
yonyou-doc2skill install-agent output/react/ --agent cursor

# Install to Windsurf
yonyou-doc2skill install-agent output/react/ --agent windsurf

# Force overwrite
yonyou-doc2skill install-agent output/react/ --agent cursor --force
```

---

### multilang

Multi-language documentation support.

**Purpose:** Scrape and merge documentation in multiple languages.

**Syntax:**
```bash
yonyou-doc2skill multilang --config CONFIG [options]
```

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| `-c` | `--config` | Config JSON file |
| | `--primary` | Primary language |
| | `--languages` | Comma-separated languages |
| | `--merge-strategy` | How to merge: parallel, hierarchical |

**Examples:**

```bash
# Multi-language scrape
yonyou-doc2skill multilang --config configs/react-i18n.json

# Specific languages
yonyou-doc2skill multilang --config configs/docs.json --languages en,zh,es
```

---

### package

Package skill directory into platform-specific format.

**Purpose:** Create uploadable packages for Claude, Gemini, OpenAI, and RAG platforms.

**Syntax:**
```bash
yonyou-doc2skill package SKILL_DIRECTORY [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `SKILL_DIRECTORY` | Yes | Path to skill directory |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| | `--target` | claude | Target platform |
| | `--no-open` | | Don't open output folder |
| | `--skip-quality-check` | | Skip quality checks |
| | `--upload` | | Auto-upload after packaging |
| | `--streaming` | | Streaming mode for large docs |
| | `--streaming-chunk-chars` | 4000 | Max chars per chunk (streaming) |
| | `--streaming-overlap-chars` | 200 | Overlap between chunks (chars) |
| | `--batch-size` | 100 | Chunks per batch |
| | `--chunk-for-rag` | | Enable RAG chunking |
| | `--chunk-tokens` | 512 | Max tokens per chunk |
| | `--chunk-overlap-tokens` | 50 | Overlap between chunks (tokens) |
| | `--no-preserve-code-blocks` | | Allow code block splitting |

**Supported Platforms:**

| Platform | Format | Flag |
|----------|--------|------|
| Claude AI | ZIP + YAML | `--target claude` |
| Google Gemini | tar.gz | `--target gemini` |
| OpenAI | ZIP + Vector | `--target openai` |
| OpenCode | Directory | `--target opencode` |
| Kimi | ZIP | `--target kimi` |
| DeepSeek | ZIP | `--target deepseek` |
| Qwen | ZIP | `--target qwen` |
| OpenRouter | ZIP | `--target openrouter` |
| Together AI | ZIP | `--target together` |
| Fireworks AI | ZIP | `--target fireworks` |
| LangChain | Documents | `--target langchain` |
| LlamaIndex | TextNodes | `--target llama-index` |
| Haystack | Documents | `--target haystack` |
| ChromaDB | Collection | `--target chroma` |
| Weaviate | Objects | `--target weaviate` |
| Qdrant | Points | `--target qdrant` |
| FAISS | Index | `--target faiss` |
| Pinecone | Markdown | `--target pinecone` |
| Markdown | ZIP | `--target markdown` |

**Examples:**

```bash
# Package for Claude (default)
yonyou-doc2skill package output/react/

# Package for Gemini
yonyou-doc2skill package output/react/ --target gemini

# Package for multiple platforms
for platform in claude gemini openai; do
  yonyou-doc2skill package output/react/ --target $platform
done

# Package with upload
yonyou-doc2skill package output/react/ --target claude --upload

# Streaming mode for large docs
yonyou-doc2skill package output/large-docs/ --streaming
```

---

### pdf

Extract content from PDF and generate skill.

**Purpose:** Convert PDF manuals, documentation, and papers into skills.

**Syntax:**
```bash
yonyou-doc2skill pdf [options]
```

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| `-c` | `--config` | PDF config JSON file |
| | `--pdf` | Direct PDF file path |
| `-n` | `--name` | Skill name |
| `-d` | `--description` | Description |
| | `--from-json` | Build from extracted JSON |
| | `--enhance-workflow` | Apply workflow preset |
| | `--enhance-stage` | Add inline stage |
| | `--var` | Override workflow variable |
| | `--workflow-dry-run` | Preview workflow |
| | `--enhance-level` | 0 | AI enhancement (default: 0 for PDF) |

**Examples:**

```bash
# Direct PDF path
yonyou-doc2skill pdf --pdf manual.pdf --name product-manual

# With config file
yonyou-doc2skill pdf --config configs/manual.json

# Enable enhancement
yonyou-doc2skill pdf --pdf manual.pdf --enhance-level 2
```

---

### quality

Analyze and score skill documentation quality.

**Purpose:** Quality assurance before packaging/uploading.

**Syntax:**
```bash
yonyou-doc2skill quality SKILL_DIRECTORY [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `SKILL_DIRECTORY` | Yes | Path to skill directory |

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| | `--report` | Generate detailed report |
| | `--threshold` | Quality threshold (0-10) |

**Examples:**

```bash
# Basic quality check
yonyou-doc2skill quality output/react/

# Detailed report
yonyou-doc2skill quality output/react/ --report

# Fail if below threshold
yonyou-doc2skill quality output/react/ --threshold 7.0
```

---

### resume

Resume interrupted scraping job from checkpoint.

**Purpose:** Continue from where a scrape failed or was interrupted.

**Syntax:**
```bash
yonyou-doc2skill resume [JOB_ID] [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `JOB_ID` | No | Job ID to resume |

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| | `--list` | List all resumable jobs |
| | `--clean` | Clean up old progress files |

**Examples:**

```bash
# List resumable jobs
yonyou-doc2skill resume --list

# Resume specific job
yonyou-doc2skill resume job-abc123

# Clean old checkpoints
yonyou-doc2skill resume --clean
```

---

### scrape

Scrape documentation website and generate skill.

**Purpose:** The main command for converting web documentation into skills.

**Syntax:**
```bash
yonyou-doc2skill scrape [url] [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `url` | No | Base documentation URL |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| `-c` | `--config` | | Config JSON file |
| `-n` | `--name` | | Skill name |
| `-d` | `--description` | | Description |
| | `--enhance-level` | 2 | AI enhancement (0-3) |
| | `--api-key` | | Anthropic API key |
| | `--enhance-workflow` | | Apply workflow preset |
| | `--enhance-stage` | | Add inline stage |
| | `--var` | | Override workflow variable |
| | `--workflow-dry-run` | | Preview workflow |
| `-i` | `--interactive` | | Interactive mode |
| | `--url` | | Base URL (alternative to positional) |
| | `--max-pages` | | Max pages to scrape |
| | `--skip-scrape` | | Use existing data |
| | `--dry-run` | | Preview without scraping |
| | `--resume` | | Resume from checkpoint |
| | `--fresh` | | Clear checkpoint |
| `-r` | `--rate-limit` | 0.5 | Rate limit in seconds |
| `-w` | `--workers` | 1 | Parallel workers (max 10) |
| | `--async` | | Enable async mode |
| | `--no-rate-limit` | | Disable rate limiting |
| | `--interactive-enhancement` | | Interactive enhancement |
| `-v` | `--verbose` | | Verbose output |
| `-q` | `--quiet` | | Quiet output |

**Examples:**

```bash
# With preset config
yonyou-doc2skill scrape --config configs/react.json

# Quick mode
yonyou-doc2skill scrape --name react --url https://react.dev/

# Interactive mode
yonyou-doc2skill scrape --interactive

# Dry run
yonyou-doc2skill scrape --config configs/react.json --dry-run

# Fast async scraping
yonyou-doc2skill scrape --config configs/react.json --async --workers 5

# Skip scrape, rebuild from cache
yonyou-doc2skill scrape --config configs/react.json --skip-scrape

# Resume interrupted scrape
yonyou-doc2skill scrape --config configs/react.json --resume
```

---

### stream

Stream large files chunk-by-chunk.

**Purpose:** Memory-efficient processing for very large documentation sites.

**Syntax:**
```bash
yonyou-doc2skill stream --config CONFIG [options]
```

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| `-c` | `--config` | Config JSON file |
| | `--streaming-chunk-chars` | Maximum characters per chunk (default: 4000) |
| | `--output` | Output directory |

**Examples:**

```bash
# Stream large documentation
yonyou-doc2skill stream --config configs/large-docs.json

# Custom chunk size
yonyou-doc2skill stream --config configs/large-docs.json --streaming-chunk-chars 1000
```

---

### unified

Multi-source scraping combining docs + GitHub + PDF.

**Purpose:** Create a single skill from multiple sources with conflict detection.

**Syntax:**
```bash
yonyou-doc2skill unified --config FILE [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `--config FILE` | Yes | Unified config JSON file |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| | `--merge-mode` | claude-enhanced | Merge mode: rule-based, claude-enhanced |
| | `--fresh` | | Clear existing data |
| | `--dry-run` | | Dry run mode |

**Examples:**

```bash
# Unified scraping
yonyou-doc2skill unified --config configs/react-unified.json

# Fresh start
yonyou-doc2skill unified --config configs/react-unified.json --fresh

# Rule-based merging
yonyou-doc2skill unified --config configs/react-unified.json --merge-mode rule-based
```

**Config Format:**
```json
{
  "name": "react-complete",
  "sources": [
    {"type": "docs", "base_url": "https://react.dev/"},
    {"type": "github", "repo": "facebook/react"}
  ]
}
```

---

### update

Update docs without full rescrape.

**Purpose:** Incremental updates for changed documentation.

**Syntax:**
```bash
yonyou-doc2skill update --config CONFIG [options]
```

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| `-c` | `--config` | Config JSON file |
| | `--since` | Update since date |
| | `--check-only` | Check for updates only |

**Examples:**

```bash
# Check for updates
yonyou-doc2skill update --config configs/react.json --check-only

# Update since specific date
yonyou-doc2skill update --config configs/react.json --since 2026-01-01

# Full update
yonyou-doc2skill update --config configs/react.json
```

---

### upload

Upload skill package to LLM platform or vector database.

**Purpose:** Deploy packaged skills to target platforms.

**Syntax:**
```bash
yonyou-doc2skill upload PACKAGE_FILE [options]
```

**Arguments:**

| Name | Required | Description |
|------|----------|-------------|
| `PACKAGE_FILE` | Yes | Path to package file (.zip, .tar.gz) |

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| | `--target` | claude | Target platform |
| | `--api-key` | | Platform API key |
| | `--chroma-url` | | ChromaDB URL |
| | `--persist-directory` | ./chroma_db | ChromaDB local directory |
| | `--embedding-function` | | Embedding function |
| | `--openai-api-key` | | OpenAI key for embeddings |
| | `--weaviate-url` | | Weaviate URL |
| | `--use-cloud` | | Use Weaviate Cloud |
| | `--cluster-url` | | Weaviate Cloud cluster URL |

**Examples:**

```bash
# Upload to Claude
yonyou-doc2skill upload output/react-claude.zip

# Upload to Gemini
yonyou-doc2skill upload output/react-gemini.tar.gz --target gemini

# Upload to ChromaDB
yonyou-doc2skill upload output/react-chroma.zip --target chroma

# Upload to Weaviate Cloud
yonyou-doc2skill upload output/react-weaviate.zip --target weaviate \
  --use-cloud --cluster-url https://xxx.weaviate.network
```

---

### video

Extract content from YouTube, Vimeo, or local video files.

**Syntax:**
```bash
yonyou-doc2skill video [options]
```

**Flags:**

| Short | Long | Default | Description |
|-------|------|---------|-------------|
| | `--url` | | YouTube/Vimeo URL |
| | `--video-file` | | Local video file path |
| | `--playlist` | | YouTube playlist URL |
| `-n` | `--name` | auto | Skill name |
| | `--visual` | | Enable visual frame analysis |
| | `--enhance-level` | 2 | AI enhancement (0-3) |
| | `--start-time` | | Start time (seconds or MM:SS or HH:MM:SS) |
| | `--end-time` | | End time |
| | `--setup` | | Auto-detect GPU and install visual dependencies |

**Examples:**

```bash
# YouTube video
yonyou-doc2skill video --url https://www.youtube.com/watch?v=... --name tutorial

# Local video with visual analysis
yonyou-doc2skill video --video-file recording.mp4 --name recording --visual

# Setup GPU-aware dependencies
yonyou-doc2skill video --setup
```

---

### word

Extract content from Word (.docx) documents.

**Syntax:**
```bash
yonyou-doc2skill word --docx FILE [options]
```

**Examples:**

```bash
yonyou-doc2skill word --docx report.docx --name report
# Or via create:
yonyou-doc2skill create report.docx
```

---

### epub

Extract content from EPUB e-books.

**Syntax:**
```bash
yonyou-doc2skill epub --epub FILE [options]
```

**Examples:**

```bash
yonyou-doc2skill epub --epub book.epub --name book
# Or via create:
yonyou-doc2skill create book.epub
```

---

### jupyter

Extract content from Jupyter Notebooks (.ipynb).

**Syntax:**
```bash
yonyou-doc2skill jupyter --notebook FILE [options]
```

**Examples:**

```bash
yonyou-doc2skill jupyter --notebook analysis.ipynb --name data-analysis
# Or via create:
yonyou-doc2skill create analysis.ipynb
```

---

### html

Extract content from local HTML files.

**Syntax:**
```bash
yonyou-doc2skill html --html-path FILE [options]
```

**Examples:**

```bash
yonyou-doc2skill html --html-path docs/index.html --name local-docs
# Or via create:
yonyou-doc2skill create page.html
```

---

### openapi

Extract API documentation from OpenAPI/Swagger specifications.

**Syntax:**
```bash
yonyou-doc2skill openapi --spec FILE [options]
```

**Examples:**

```bash
yonyou-doc2skill openapi --spec api-spec.yaml --name my-api
# Or via create:
yonyou-doc2skill create api-spec.yaml
```

---

### asciidoc

Extract content from AsciiDoc files.

**Syntax:**
```bash
yonyou-doc2skill asciidoc --asciidoc-path FILE [options]
```

**Examples:**

```bash
yonyou-doc2skill asciidoc --asciidoc-path guide.adoc --name guide
# Or via create:
yonyou-doc2skill create guide.adoc
```

---

### pptx

Extract content from PowerPoint (.pptx) presentations.

**Syntax:**
```bash
yonyou-doc2skill pptx --pptx FILE [options]
```

**Examples:**

```bash
yonyou-doc2skill pptx --pptx slides.pptx --name presentation
# Or via create:
yonyou-doc2skill create slides.pptx
```

---

### rss

Extract content from RSS/Atom feeds.

**Syntax:**
```bash
yonyou-doc2skill rss [options]
```

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| | `--feed-url` | RSS/Atom feed URL |
| | `--feed-path` | Local RSS/Atom file path |
| `-n` | `--name` | Skill name |

**Examples:**

```bash
yonyou-doc2skill rss --feed-url https://blog.example.com/feed --name blog
yonyou-doc2skill rss --feed-path feed.rss --name feed
# Or via create:
yonyou-doc2skill create feed.rss
```

---

### manpage

Extract content from Unix man pages.

**Syntax:**
```bash
yonyou-doc2skill manpage --man-path FILE [options]
```

**Examples:**

```bash
yonyou-doc2skill manpage --man-path curl.1 --name curl-docs
# Or via create:
yonyou-doc2skill create curl.1
```

---

### confluence

Extract content from Confluence wikis.

**Syntax:**
```bash
yonyou-doc2skill confluence [options]
```

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| | `--space-key` | Confluence space key |
| | `--base-url` | Confluence base URL |
| | `--export-path` | Path to Confluence export directory |
| `-n` | `--name` | Skill name |

**Examples:**

```bash
# From Confluence API
yonyou-doc2skill confluence --space-key DEV --base-url https://wiki.example.com --name team-wiki

# From Confluence export
yonyou-doc2skill confluence --export-path ./confluence-export/ --name wiki
```

---

### notion

Extract content from Notion pages and databases.

**Syntax:**
```bash
yonyou-doc2skill notion [options]
```

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| | `--database-id` | Notion database ID |
| | `--page-id` | Notion page ID |
| | `--export-path` | Path to Notion export directory |
| `-n` | `--name` | Skill name |

**Examples:**

```bash
# From Notion API
yonyou-doc2skill notion --database-id abc123 --name my-notes

# From Notion export
yonyou-doc2skill notion --export-path ./notion-export/ --name notes
```

---

### chat

Extract content from Slack/Discord chat exports.

**Syntax:**
```bash
yonyou-doc2skill chat --export-path DIR [options]
```

**Examples:**

```bash
yonyou-doc2skill chat --export-path ./slack-export/ --name team-chat
yonyou-doc2skill chat --export-path ./discord-export/ --name server-archive
```

---

### workflows

Manage enhancement workflow presets.

**Purpose:** List, inspect, copy, add, remove, and validate YAML workflow presets.

**Syntax:**
```bash
yonyou-doc2skill workflows ACTION [options]
```

**Actions:**

| Action | Description |
|--------|-------------|
| `list` | List all workflows (bundled + user) |
| `show` | Print YAML content of workflow |
| `copy` | Copy bundled workflow to user dir |
| `add` | Install custom YAML workflow |
| `remove` | Delete user workflow |
| `validate` | Validate workflow file |

**Flags:**

| Short | Long | Description |
|-------|------|-------------|
| | `--name` | Custom name for add action |

**Examples:**

```bash
# List all workflows
yonyou-doc2skill workflows list

# Show workflow content
yonyou-doc2skill workflows show security-focus

# Copy for editing
yonyou-doc2skill workflows copy security-focus

# Add custom workflow
yonyou-doc2skill workflows add ./my-workflow.yaml

# Add with custom name
yonyou-doc2skill workflows add ./workflow.yaml --name my-custom

# Remove user workflow
yonyou-doc2skill workflows remove my-workflow

# Validate workflow
yonyou-doc2skill workflows validate security-focus
yonyou-doc2skill workflows validate ./my-workflow.yaml
```

**Built-in Presets:**
- `default` - Standard enhancement
- `minimal` - Light enhancement
- `security-focus` - Security analysis (4 stages)
- `architecture-comprehensive` - Deep architecture review (7 stages)
- `api-documentation` - API docs focus (3 stages)

---

## Common Workflows

### Workflow 1: Documentation → Skill

```bash
# 1. Estimate pages (optional)
yonyou-doc2skill estimate configs/react.json

# 2. Scrape documentation
yonyou-doc2skill scrape --config configs/react.json

# 3. Enhance SKILL.md (optional, recommended)
yonyou-doc2skill enhance output/react/

# 4. Package for Claude
yonyou-doc2skill package output/react/ --target claude

# 5. Upload
yonyou-doc2skill upload output/react-claude.zip
```

### Workflow 2: GitHub → Skill

```bash
# 1. Analyze repository
yonyou-doc2skill github --repo facebook/react

# 2. Package
yonyou-doc2skill package output/react/ --target claude

# 3. Upload
yonyou-doc2skill upload output/react-claude.zip
```

### Workflow 3: Local Codebase → Skill

```bash
# 1. Analyze codebase
yonyou-doc2skill analyze --directory ./my-project

# 2. Package
yonyou-doc2skill package output/codebase/ --target claude

# 3. Install to Cursor
yonyou-doc2skill install-agent output/codebase/ --agent cursor
```

### Workflow 4: PDF → Skill

```bash
# 1. Extract PDF
yonyou-doc2skill pdf --pdf manual.pdf --name product-docs

# 2. Package
yonyou-doc2skill package output/product-docs/ --target claude
```

### Workflow 5: Multi-Source → Skill

```bash
# 1. Create unified config (configs/my-project.json)
# 2. Run unified scraping
yonyou-doc2skill unified --config configs/my-project.json

# 3. Package
yonyou-doc2skill package output/my-project/ --target claude
```

### Workflow 6: One-Command Complete

```bash
# Everything in one command
yonyou-doc2skill install --config react --destination ./output

# Or with create
yonyou-doc2skill create https://docs.react.dev/ --preset standard
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error |
| `2` | Warning (e.g., estimation hit limit) |
| `130` | Interrupted by user (Ctrl+C) |

---

## Troubleshooting

### Command not found
```bash
# Ensure package is installed
pip install yonyou-doc2skill

# Check PATH
which yonyou-doc2skill
```

### ImportError
```bash
# Install in editable mode (development)
pip install -e .
```

### Rate limiting
```bash
# Increase rate limit
yonyou-doc2skill scrape --config react.json --rate-limit 1.0
```

### Out of memory
```bash
# Use streaming mode
yonyou-doc2skill package output/large/ --streaming
```

---

## See Also

- [Config Format](CONFIG_FORMAT.md) - JSON configuration specification
- [Environment Variables](ENVIRONMENT_VARIABLES.md) - Complete env var reference
- [MCP Reference](MCP_REFERENCE.md) - MCP tools documentation

---

*For additional help: `yonyou-doc2skill --help` or `yonyou-doc2skill <command> --help`*
