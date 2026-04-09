# Scraping Guide

> **Yonyou Doc2Skill v3.1.0**  
> **Complete guide to all scraping options**

---

## Overview

Yonyou Doc2Skill can extract knowledge from four types of sources:

| Source | Command | Best For |
|--------|---------|----------|
| **Documentation** | `create <url>` | Web docs, tutorials, API refs |
| **GitHub** | `create <repo>` | Source code, issues, releases |
| **PDF** | `create <file.pdf>` | Manuals, papers, reports |
| **Local** | `create <./path>` | Your projects, internal code |

---

## Documentation Scraping

### Basic Usage

```bash
# Auto-detect and scrape
yonyou-doc2skill create https://docs.react.dev/

# With custom name
yonyou-doc2skill create https://docs.react.dev/ --name react-docs

# With description
yonyou-doc2skill create https://docs.react.dev/ \
  --description "React JavaScript library documentation"
```

### Using Preset Configs

```bash
# List available presets
yonyou-doc2skill estimate --all

# Use preset
yonyou-doc2skill create --config react
yonyou-doc2skill create --config django
yonyou-doc2skill create --config fastapi
```

**Available presets:** See `configs/` directory in repository.

### Custom Configuration

```bash
# Create config file
cat > configs/my-docs.json << 'EOF'
{
  "name": "my-framework",
  "base_url": "https://docs.example.com/",
  "description": "My framework documentation",
  "max_pages": 200,
  "rate_limit": 0.5,
  "selectors": {
    "main_content": "article",
    "title": "h1"
  },
  "url_patterns": {
    "include": ["/docs/", "/api/"],
    "exclude": ["/blog/", "/search"]
  }
}
EOF

# Use config
yonyou-doc2skill create --config configs/my-docs.json
```

See [Config Format](../reference/CONFIG_FORMAT.md) for all options.

### Advanced Options

```bash
# Limit pages (for testing)
yonyou-doc2skill create <url> --max-pages 50

# Adjust rate limit
yonyou-doc2skill create <url> --rate-limit 1.0

# Parallel workers (faster)
yonyou-doc2skill create <url> --workers 5 --async

# Dry run (preview)
yonyou-doc2skill create <url> --dry-run

# Resume interrupted
yonyou-doc2skill create <url> --resume

# Fresh start (ignore cache)
yonyou-doc2skill create <url> --fresh
```

---

## GitHub Repository Scraping

### Basic Usage

```bash
# By repo name
yonyou-doc2skill create facebook/react

# With explicit flag
yonyou-doc2skill github --repo facebook/react

# With custom name
yonyou-doc2skill github --repo facebook/react --name react-source
```

### With GitHub Token

```bash
# Set token for higher rate limits
export GITHUB_TOKEN=ghp_...

# Use token
yonyou-doc2skill github --repo facebook/react
```

**Benefits of token:**
- 5000 requests/hour vs 60
- Access to private repos
- Higher GraphQL limits

### What Gets Extracted

| Data | Default | Flag to Disable |
|------|---------|-----------------|
| Source code | ✅ | `--scrape-only` |
| README | ✅ | - |
| Issues | ✅ | `--no-issues` |
| Releases | ✅ | `--no-releases` |
| Changelog | ✅ | `--no-changelog` |

### Control What to Fetch

```bash
# Skip issues (faster)
yonyou-doc2skill github --repo facebook/react --no-issues

# Limit issues
yonyou-doc2skill github --repo facebook/react --max-issues 50

# Scrape only (no build)
yonyou-doc2skill github --repo facebook/react --scrape-only

# Non-interactive (CI/CD)
yonyou-doc2skill github --repo facebook/react --non-interactive
```

---

## PDF Extraction

### Basic Usage

```bash
# Direct file
yonyou-doc2skill create manual.pdf --name product-manual

# With explicit command
yonyou-doc2skill pdf --pdf manual.pdf --name docs
```

### OCR for Scanned PDFs

```bash
# Enable OCR
yonyou-doc2skill pdf --pdf scanned.pdf --enable-ocr
```

**Requirements:**
```bash
pip install yonyou-doc2skill[pdf-ocr]
# Also requires: tesseract-ocr (system package)
```

### Password-Protected PDFs

```bash
# In config file
{
  "name": "secure-docs",
  "pdf_path": "protected.pdf",
  "password": "secret123"
}
```

### Page Range

```bash
# Extract specific pages (via config)
{
  "pdf_path": "manual.pdf",
  "page_range": [1, 100]
}
```

---

## Local Codebase Analysis

### Basic Usage

```bash
# Current directory
yonyou-doc2skill create .

# Specific directory
yonyou-doc2skill create ./my-project

# With explicit command
yonyou-doc2skill analyze --directory ./my-project
```

### Analysis Presets

```bash
# Quick analysis (1-2 min)
yonyou-doc2skill analyze --directory ./my-project --preset quick

# Standard analysis (5-10 min) - default
yonyou-doc2skill analyze --directory ./my-project --preset standard

# Comprehensive (20-60 min)
yonyou-doc2skill analyze --directory ./my-project --preset comprehensive
```

### What Gets Analyzed

| Feature | Quick | Standard | Comprehensive |
|---------|-------|----------|---------------|
| Code structure | ✅ | ✅ | ✅ |
| API extraction | ✅ | ✅ | ✅ |
| Comments | - | ✅ | ✅ |
| Patterns | - | ✅ | ✅ |
| Test examples | - | - | ✅ |
| How-to guides | - | - | ✅ |
| Config patterns | - | - | ✅ |

### Language Filtering

```bash
# Specific languages
yonyou-doc2skill analyze --directory ./my-project \
  --languages Python,JavaScript

# File patterns
yonyou-doc2skill analyze --directory ./my-project \
  --file-patterns "*.py,*.js"
```

### Skip Features

```bash
# Skip heavy features
yonyou-doc2skill analyze --directory ./my-project \
  --skip-dependency-graph \
  --skip-patterns \
  --skip-test-examples
```

---

## Common Scraping Patterns

### Pattern 1: Test First

```bash
# Dry run to preview
yonyou-doc2skill create <source> --dry-run

# Small test scrape
yonyou-doc2skill create <source> --max-pages 10

# Full scrape
yonyou-doc2skill create <source>
```

### Pattern 2: Iterative Development

```bash
# Scrape without enhancement (fast)
yonyou-doc2skill create <source> --enhance-level 0

# Review output
ls output/my-skill/
cat output/my-skill/SKILL.md

# Enhance later
yonyou-doc2skill enhance output/my-skill/
```

### Pattern 3: Parallel Processing

```bash
# Fast async scraping
yonyou-doc2skill create <url> --async --workers 5

# Even faster (be careful with rate limits)
yonyou-doc2skill create <url> --async --workers 10 --rate-limit 0.2
```

### Pattern 4: Resume Capability

```bash
# Start scraping
yonyou-doc2skill create <source>
# ...interrupted...

# Resume later
yonyou-doc2skill resume --list
yonyou-doc2skill resume <job-id>
```

---

## Troubleshooting Scraping

### "No content extracted"

**Problem:** Wrong CSS selectors

**Solution:**
```bash
# Find correct selectors
curl -s <url> | grep -i 'article\|main\|content'

# Update config
{
  "selectors": {
    "main_content": "div.content"  // or "article", "main", etc.
  }
}
```

### "Rate limit exceeded"

**Problem:** Too many requests

**Solution:**
```bash
# Slow down
yonyou-doc2skill create <url> --rate-limit 2.0

# Or use GitHub token for GitHub repos
export GITHUB_TOKEN=ghp_...
```

### "Too many pages"

**Problem:** Site is larger than expected

**Solution:**
```bash
# Estimate first
yonyou-doc2skill estimate configs/my-config.json

# Limit pages
yonyou-doc2skill create <url> --max-pages 100

# Adjust URL patterns
{
  "url_patterns": {
    "exclude": ["/blog/", "/archive/", "/search"]
  }
}
```

### "Memory error"

**Problem:** Site too large for memory

**Solution:**
```bash
# Use streaming mode
yonyou-doc2skill create <url> --streaming

# Or smaller chunks
yonyou-doc2skill create <url> --chunk-tokens 500
```

---

## Performance Tips

| Tip | Command | Impact |
|-----|---------|--------|
| Use presets | `--config react` | Faster setup |
| Async mode | `--async --workers 5` | 3-5x faster |
| Skip enhancement | `--enhance-level 0` | Skip 60 sec |
| Use cache | `--skip-scrape` | Instant rebuild |
| Resume | `--resume` | Continue interrupted |

---

## Next Steps

- [Enhancement Guide](03-enhancement.md) - Improve skill quality
- [Packaging Guide](04-packaging.md) - Export to platforms
- [Config Format](../reference/CONFIG_FORMAT.md) - Advanced configuration
