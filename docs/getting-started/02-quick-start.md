# Quick Start Guide

> **Yonyou Doc2Skill v3.2.0**  
> **Create your first skill in 3 commands**

---

## The 3 Commands

```bash
# 1. Install Yonyou Doc2Skill
pip install yonyou-doc2skill

# 2. Create a skill from any source
yonyou-doc2skill create https://docs.django.com/

# 3. Package it for your AI platform
yonyou-doc2skill package output/django --target claude
```

**That's it!** You now have `output/django-claude.zip` ready to upload.

---

## What You Can Create From

The `create` command auto-detects your source:

| Source Type | Example Command |
|-------------|-----------------|
| **Documentation** | `yonyou-doc2skill create https://docs.react.dev/` |
| **GitHub Repo** | `yonyou-doc2skill create facebook/react` |
| **Local Code** | `yonyou-doc2skill create ./my-project` |
| **PDF File** | `yonyou-doc2skill create manual.pdf` |
| **Word Document** | `yonyou-doc2skill create report.docx` |
| **EPUB Book** | `yonyou-doc2skill create book.epub` |
| **Video** | `yonyou-doc2skill create https://youtube.com/watch?v=...` |
| **Jupyter Notebook** | `yonyou-doc2skill create analysis.ipynb` |
| **Local HTML** | `yonyou-doc2skill create page.html` |
| **OpenAPI Spec** | `yonyou-doc2skill create api-spec.yaml` |
| **AsciiDoc** | `yonyou-doc2skill create guide.adoc` |
| **PowerPoint** | `yonyou-doc2skill create slides.pptx` |
| **RSS/Atom Feed** | `yonyou-doc2skill create feed.rss` |
| **Man Page** | `yonyou-doc2skill create grep.1` |
| **Confluence** | `yonyou-doc2skill confluence --space DEV` |
| **Notion** | `yonyou-doc2skill notion --database abc123` |
| **Slack/Discord** | `yonyou-doc2skill chat --export slack-export/` |
| **Config File** | `yonyou-doc2skill create configs/custom.json` |

---

## Examples by Source

### Documentation Website

```bash
# React documentation
yonyou-doc2skill create https://react.dev/
yonyou-doc2skill package output/react --target claude

# Django documentation  
yonyou-doc2skill create https://docs.djangoproject.com/
yonyou-doc2skill package output/django --target claude
```

### GitHub Repository

```bash
# React source code
yonyou-doc2skill create facebook/react
yonyou-doc2skill package output/react --target claude

# Your own repo
yonyou-doc2skill create yourusername/yourrepo
yonyou-doc2skill package output/yourrepo --target claude
```

### Local Project

```bash
# Your codebase
yonyou-doc2skill create ./my-project
yonyou-doc2skill package output/my-project --target claude

# Specific directory
cd ~/projects/my-api
yonyou-doc2skill create .
yonyou-doc2skill package output/my-api --target claude
```

### PDF Document

```bash
# Technical manual
yonyou-doc2skill create manual.pdf --name product-docs
yonyou-doc2skill package output/product-docs --target claude

# Research paper
yonyou-doc2skill create paper.pdf --name research
yonyou-doc2skill package output/research --target claude
```

### Video

```bash
# YouTube video transcript
yonyou-doc2skill create https://www.youtube.com/watch?v=dQw4w9WgXcQ --name tutorial
yonyou-doc2skill package output/tutorial --target claude
```

### Jupyter Notebook

```bash
# Data science notebook
yonyou-doc2skill create analysis.ipynb --name ml-analysis
yonyou-doc2skill package output/ml-analysis --target claude
```

### PowerPoint / Word / EPUB

```bash
# PowerPoint slides
yonyou-doc2skill create presentation.pptx --name quarterly-review

# Word document
yonyou-doc2skill create spec.docx --name api-spec

# EPUB book
yonyou-doc2skill create rust-book.epub --name rust-guide
```

### Confluence / Notion / Slack

```bash
# Confluence wiki space
yonyou-doc2skill confluence --space DEV --name team-docs

# Notion workspace
yonyou-doc2skill notion --database abc123 --name product-wiki

# Slack/Discord export
yonyou-doc2skill chat --export slack-export/ --name team-chat
```

---

## Common Options

### Specify a Name

```bash
yonyou-doc2skill create https://docs.example.com/ --name my-docs
```

### Add Description

```bash
yonyou-doc2skill create facebook/react --description "React source code analysis"
```

### Dry Run (Preview)

```bash
yonyou-doc2skill create https://docs.react.dev/ --dry-run
```

### Skip Enhancement (Faster)

```bash
yonyou-doc2skill create https://docs.react.dev/ --enhance-level 0
```

### Use a Preset

```bash
# Quick analysis (1-2 min)
yonyou-doc2skill create ./my-project --preset quick

# Comprehensive analysis (20-60 min)
yonyou-doc2skill create ./my-project --preset comprehensive
```

---

## Package for Different Platforms

### Claude AI (Default)

```bash
yonyou-doc2skill package output/my-skill/
# Creates: output/my-skill-claude.zip
```

### Google Gemini

```bash
yonyou-doc2skill package output/my-skill/ --target gemini
# Creates: output/my-skill-gemini.tar.gz
```

### OpenAI ChatGPT

```bash
yonyou-doc2skill package output/my-skill/ --target openai
# Creates: output/my-skill-openai.zip
```

### LangChain

```bash
yonyou-doc2skill package output/my-skill/ --target langchain
# Creates: output/my-skill-langchain/ directory
```

### Multiple Platforms

```bash
for platform in claude gemini openai; do
  yonyou-doc2skill package output/my-skill/ --target $platform
done
```

---

## Upload to Platform

### Upload to Claude

```bash
export ANTHROPIC_API_KEY=sk-ant-...
yonyou-doc2skill upload output/my-skill-claude.zip --target claude
```

### Upload to Gemini

```bash
export GOOGLE_API_KEY=AIza...
yonyou-doc2skill upload output/my-skill-gemini.tar.gz --target gemini
```

### Auto-Upload After Package

```bash
export ANTHROPIC_API_KEY=sk-ant-...
yonyou-doc2skill package output/my-skill/ --target claude --upload
```

---

## Complete One-Command Workflow

Use `install` for everything in one step:

```bash
# Complete: scrape → enhance → package → upload
export ANTHROPIC_API_KEY=sk-ant-...
yonyou-doc2skill install --config react --target claude

# Skip upload
yonyou-doc2skill install --config react --target claude --no-upload
```

---

## Output Structure

After running `create`, you'll have:

```
output/
├── django/                    # The skill
│   ├── SKILL.md              # Main skill file
│   ├── references/           # Organized documentation
│   │   ├── index.md
│   │   ├── getting_started.md
│   │   └── api_reference.md
│   └── .yonyou-doc2skill/       # Metadata
│
└── django-claude.zip         # Packaged skill (after package)
```

---

## Time Estimates

| Source Type | Size | Time |
|-------------|------|------|
| Small docs (< 50 pages) | ~10 MB | 2-5 min |
| Medium docs (50-200 pages) | ~50 MB | 10-20 min |
| Large docs (200-500 pages) | ~200 MB | 30-60 min |
| GitHub repo (< 1000 files) | varies | 5-15 min |
| Local project | varies | 2-10 min |
| PDF (< 100 pages) | ~5 MB | 1-3 min |

*Times include scraping + enhancement (level 2). Use `--enhance-level 0` to skip enhancement.*

---

## Quick Tips

### Test First with Dry Run

```bash
yonyou-doc2skill create https://docs.example.com/ --dry-run
```

### Use Presets for Faster Results

```bash
# Quick mode for testing
yonyou-doc2skill create https://docs.react.dev/ --preset quick
```

### Skip Enhancement for Speed

```bash
yonyou-doc2skill create https://docs.react.dev/ --enhance-level 0
yonyou-doc2skill enhance output/react/  # Enhance later
```

### Check Available Configs

```bash
yonyou-doc2skill estimate --all
```

### Resume Interrupted Jobs

```bash
yonyou-doc2skill resume --list
yonyou-doc2skill resume <job-id>
```

---

## Next Steps

- [Your First Skill](03-your-first-skill.md) - Complete walkthrough
- [Core Concepts](../user-guide/01-core-concepts.md) - Understand how it works
- [Scraping Guide](../user-guide/02-scraping.md) - All scraping options

---

## Troubleshooting

### "command not found"

```bash
# Add to PATH
export PATH="$HOME/.local/bin:$PATH"
```

### "No module named 'yonyou_doc2skill'"

```bash
# Reinstall
pip install --force-reinstall yonyou-doc2skill
```

### Scraping too slow

```bash
# Use async mode
yonyou-doc2skill create https://docs.react.dev/ --async --workers 5
```

### Out of memory

```bash
# Use streaming mode
yonyou-doc2skill package output/large-skill/ --streaming
```

---

## See Also

- [Installation Guide](01-installation.md) - Detailed installation
- [CLI Reference](../reference/CLI_REFERENCE.md) - All commands
- [Config Format](../reference/CONFIG_FORMAT.md) - Custom configurations
