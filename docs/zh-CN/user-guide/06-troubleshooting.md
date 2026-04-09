# Troubleshooting Guide

> **Yonyou Doc2Skill v3.1.0**  
> **Common issues and solutions**

---

## Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| `command not found` | `export PATH="$HOME/.local/bin:$PATH"` |
| `ImportError` | `pip install -e .` |
| `Rate limit` | Add `--rate-limit 2.0` |
| `No content` | Check selectors in config |
| `Enhancement fails` | Set `ANTHROPIC_API_KEY` |
| `Out of memory` | Use `--streaming` mode |

---

## Installation Issues

### "command not found: yonyou-doc2skill"

**Cause:** pip bin directory not in PATH

**Solution:**
```bash
# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Or reinstall with --user
pip install --user --force-reinstall yonyou-doc2skill

# Verify
which yonyou-doc2skill
```

---

### "No module named 'yonyou_doc2skill'"

**Cause:** Package not installed or wrong Python environment

**Solution:**
```bash
# Install package
pip install yonyou-doc2skill

# For development
pip install -e .

# Verify
python -c "import yonyou_doc2skill; print(yonyou_doc2skill.__version__)"
```

---

### "Permission denied"

**Cause:** Trying to install system-wide

**Solution:**
```bash
# Don't use sudo
# Instead:
pip install --user yonyou-doc2skill

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install yonyou-doc2skill
```

---

## Scraping Issues

### "Rate limit exceeded"

**Cause:** Too many requests to server

**Solution:**
```bash
# Slow down
yonyou-doc2skill create <url> --rate-limit 2.0

# For GitHub
export GITHUB_TOKEN=ghp_...
yonyou-doc2skill github --repo owner/repo
```

---

### "No content extracted"

**Cause:** Wrong CSS selectors

**Solution:**
```bash
# Find correct selectors
curl -s <url> | grep -i 'article\|main\|content'

# Create config with correct selectors
cat > configs/fix.json << 'EOF'
{
  "name": "my-site",
  "base_url": "https://example.com/",
  "selectors": {
    "main_content": "article"  # or "main", ".content", etc.
  }
}
EOF

yonyou-doc2skill create --config configs/fix.json
```

**Common selectors:**
| Site Type | Selector |
|-----------|----------|
| Docusaurus | `article` |
| ReadTheDocs | `[role="main"]` |
| GitBook | `.book-body` |
| MkDocs | `.md-content` |

---

### "Too many pages"

**Cause:** Site larger than max_pages setting

**Solution:**
```bash
# Estimate first
yonyou-doc2skill estimate configs/my-config.json

# Increase limit
yonyou-doc2skill create <url> --max-pages 1000

# Or limit in config
{
  "max_pages": 1000
}
```

---

### "Connection timeout"

**Cause:** Slow server or network issues

**Solution:**
```bash
# Increase timeout
yonyou-doc2skill create <url> --timeout 60

# Or in config
{
  "timeout": 60
}
```

---

### "SSL certificate error"

**Cause:** Certificate validation failure

**Solution:**
```bash
# Set environment variable (not recommended for production)
export PYTHONWARNINGS="ignore:Unverified HTTPS request"

# Or use requests settings in config
{
  "verify_ssl": false
}
```

---

## Enhancement Issues

### "Enhancement failed: No API key"

**Cause:** ANTHROPIC_API_KEY not set

**Solution:**
```bash
# Set API key
export ANTHROPIC_API_KEY=sk-ant-...

# Or use LOCAL mode
yonyou-doc2skill enhance output/my-skill/ --agent local
```

---

### "Claude Code not found" (LOCAL mode)

**Cause:** Claude Code not installed

**Solution:**
```bash
# Install Claude Code
# See: https://claude.ai/code

# Or use API mode
export ANTHROPIC_API_KEY=sk-ant-...
yonyou-doc2skill enhance output/my-skill/ --agent api
```

---

### "Enhancement timeout"

**Cause:** Enhancement taking too long

**Solution:**
```bash
# Increase timeout
yonyou-doc2skill enhance output/my-skill/ --timeout 1200

# Use background mode
yonyou-doc2skill enhance output/my-skill/ --background
yonyou-doc2skill enhance-status output/my-skill/ --watch
```

---

### "Workflow not found"

**Cause:** Typo or workflow doesn't exist

**Solution:**
```bash
# List available workflows
yonyou-doc2skill workflows list

# Check spelling
yonyou-doc2skill create <source> --enhance-workflow security-focus
```

---

## Packaging Issues

### "Package validation failed"

**Cause:** SKILL.md missing or malformed

**Solution:**
```bash
# Check structure
ls output/my-skill/

# Should contain:
# - SKILL.md
# - references/

# Rebuild if needed
yonyou-doc2skill create --config my-config --skip-scrape

# Or recreate
yonyou-doc2skill create <source>
```

---

### "Target platform not supported"

**Cause:** Typo in target name

**Solution:**
```bash
# List valid targets
yonyou-doc2skill package --help

# Valid targets:
# claude, gemini, openai, langchain, llama-index,
# haystack, pinecone, chroma, weaviate, qdrant, faiss, markdown
```

---

### "Out of memory"

**Cause:** Skill too large for available RAM

**Solution:**
```bash
# Use streaming mode
yonyou-doc2skill package output/my-skill/ --streaming

# Reduce chunk size
yonyou-doc2skill package output/my-skill/ \
  --streaming \
  --streaming-chunk-chars 1000
```

---

## Upload Issues

### "Upload failed: Invalid API key"

**Cause:** Wrong or missing API key

**Solution:**
```bash
# Claude
export ANTHROPIC_API_KEY=sk-ant-...

# Gemini
export GOOGLE_API_KEY=AIza...

# OpenAI
export OPENAI_API_KEY=sk-...

# Verify
echo $ANTHROPIC_API_KEY
```

---

### "Upload failed: Network error"

**Cause:** Connection issues

**Solution:**
```bash
# Check connection
ping api.anthropic.com

# Retry
yonyou-doc2skill upload output/my-skill-claude.zip --target claude

# Or upload manually through web interface
```

---

### "Upload failed: File too large"

**Cause:** Package exceeds platform limits

**Solution:**
```bash
# Check size
ls -lh output/my-skill-claude.zip

# Use streaming mode
yonyou-doc2skill package output/my-skill/ --streaming

# Or split into smaller skills
yonyou-doc2skill workflows split-config configs/my-config.json
```

---

## GitHub Issues

### "GitHub API rate limit"

**Cause:** Unauthenticated requests limited to 60/hour

**Solution:**
```bash
# Set token
export GITHUB_TOKEN=ghp_...

# Create token: https://github.com/settings/tokens
# Needs: repo, read:org (for private repos)
```

---

### "Repository not found"

**Cause:** Private repo or wrong name

**Solution:**
```bash
# Check repo exists
https://github.com/owner/repo

# Set token for private repos
export GITHUB_TOKEN=ghp_...

# Correct format
yonyou-doc2skill github --repo owner/repo
```

---

### "No code found"

**Cause:** Empty repo or wrong branch

**Solution:**
```bash
# Check repo has code

# Specify branch in config
{
  "type": "github",
  "repo": "owner/repo",
  "branch": "main"
}
```

---

## PDF Issues

### "PDF is encrypted"

**Cause:** Password-protected PDF

**Solution:**
```bash
# Add password to config
{
  "type": "pdf",
  "pdf_path": "protected.pdf",
  "password": "secret123"
}
```

---

### "OCR failed"

**Cause:** Scanned PDF without OCR

**Solution:**
```bash
# Enable OCR
yonyou-doc2skill pdf --pdf scanned.pdf --enable-ocr

# Install OCR dependencies
pip install yonyou-doc2skill[pdf-ocr]
# System: apt-get install tesseract-ocr
```

---

## Configuration Issues

### "Invalid config JSON"

**Cause:** Syntax error in config file

**Solution:**
```bash
# Validate JSON
python -m json.tool configs/my-config.json

# Or use online validator
# jsonlint.com
```

---

### "Config not found"

**Cause:** Wrong path or missing file

**Solution:**
```bash
# Check file exists
ls configs/my-config.json

# Use absolute path
yonyou-doc2skill create --config /full/path/to/config.json

# Or list available
yonyou-doc2skill estimate --all
```

---

## Performance Issues

### "Scraping is too slow"

**Solutions:**
```bash
# Use async mode
yonyou-doc2skill create <url> --async --workers 5

# Reduce rate limit (for your own servers)
yonyou-doc2skill create <url> --rate-limit 0.1

# Skip enhancement
yonyou-doc2skill create <url> --enhance-level 0
```

---

### "Out of disk space"

**Solutions:**
```bash
# Check usage
du -sh output/

# Clean old skills
rm -rf output/old-skill/

# Use streaming mode
yonyou-doc2skill create <url> --streaming
```

---

### "High memory usage"

**Solutions:**
```bash
# Use streaming mode
yonyou-doc2skill create <url> --streaming
yonyou-doc2skill package output/my-skill/ --streaming

# Reduce workers
yonyou-doc2skill create <url> --workers 1

# Limit pages
yonyou-doc2skill create <url> --max-pages 100
```

---

## Getting Help

### Debug Mode

```bash
# Enable verbose logging
yonyou-doc2skill create <source> --verbose

# Or environment variable
export SKILL_SEEKERS_DEBUG=1
```

### Check Logs

```bash
# Enable file logging
export SKILL_SEEKERS_LOG_FILE=/tmp/yonyou-doc2skill.log

# Tail logs
tail -f /tmp/yonyou-doc2skill.log
```

### Create Minimal Reproduction

```bash
# Create test config
cat > test-config.json << 'EOF'
{
  "name": "test",
  "base_url": "https://example.com/",
  "max_pages": 5
}
EOF

# Run with debug
yonyou-doc2skill create --config test-config.json --verbose --dry-run
```

---

## Report an Issue

If none of these solutions work:

1. **Gather info:**
   ```bash
   yonyou-doc2skill --version
   python --version
   pip show yonyou-doc2skill
   ```

2. **Enable debug:**
   ```bash
   yonyou-doc2skill <command> --verbose 2>&1 | tee debug.log
   ```

3. **Create issue:**
   - https://github.com/yonyou/yonyou-doc2skill/issues
   - Include: error message, command used, debug log

---

## Error Reference

| Error Code | Meaning | Solution |
|------------|---------|----------|
| `E001` | Config not found | Check path |
| `E002` | Invalid config | Validate JSON |
| `E003` | Network error | Check connection |
| `E004` | Rate limited | Slow down or use token |
| `E005` | Scraping failed | Check selectors |
| `E006` | Enhancement failed | Check API key |
| `E007` | Packaging failed | Check skill structure |
| `E008` | Upload failed | Check API key |

---

## Still Stuck?

- **Documentation:** https://docs.yonyou.example/yonyou-doc2skill/
- **GitHub Issues:** https://github.com/yonyou/yonyou-doc2skill/issues
- **Discussions:** Share your use case

---

*Last updated: 2026-02-16*
