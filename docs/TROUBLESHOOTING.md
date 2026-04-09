# Troubleshooting Guide

Comprehensive guide for diagnosing and resolving common issues with Yonyou Doc2Skill.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Configuration Issues](#configuration-issues)
- [Scraping Issues](#scraping-issues)
- [GitHub API Issues](#github-api-issues)
- [API & Enhancement Issues](#api--enhancement-issues)
- [Docker & Kubernetes Issues](#docker--kubernetes-issues)
- [Performance Issues](#performance-issues)
- [Storage Issues](#storage-issues)
- [Network Issues](#network-issues)
- [General Debug Techniques](#general-debug-techniques)
- [Source-Type-Specific Issues](#source-type-specific-issues)

## Installation Issues

### Issue: Package Installation Fails

**Symptoms:**
```
ERROR: Could not build wheels for...
ERROR: Failed building wheel for...
```

**Solutions:**

```bash
# Update pip and setuptools
python -m pip install --upgrade pip setuptools wheel

# Install build dependencies (Ubuntu/Debian)
sudo apt install python3-dev build-essential libssl-dev

# Install build dependencies (RHEL/CentOS)
sudo yum install python3-devel gcc gcc-c++ openssl-devel

# Retry installation
pip install yonyou-doc2skill
```

### Issue: Command Not Found After Installation

**Symptoms:**
```bash
$ yonyou-doc2skill --version
bash: yonyou-doc2skill: command not found
```

**Solutions:**

```bash
# Check if installed
pip show yonyou-doc2skill

# Add to PATH
export PATH="$HOME/.local/bin:$PATH"

# Or reinstall with --user flag
pip install --user yonyou-doc2skill

# Verify
which yonyou-doc2skill
```

### Issue: Python Version Mismatch

**Symptoms:**
```
ERROR: Package requires Python >=3.10 but you are running 3.9
```

**Solutions:**

```bash
# Check Python version
python --version
python3 --version

# Use specific Python version
python3.12 -m pip install yonyou-doc2skill

# Create alias
alias python=python3.12

# Or use pyenv
pyenv install 3.12
pyenv global 3.12
```

### Issue: Video Visual Dependencies Missing

**Symptoms:**
```
Missing video dependencies: easyocr
RuntimeError: Required video visual dependencies not installed
```

**Solutions:**

```bash
# Run the GPU-aware setup command
yonyou-doc2skill video --setup

# This auto-detects your GPU and installs:
# - PyTorch (correct CUDA/ROCm/CPU variant)
# - easyocr, opencv, pytesseract, scenedetect, faster-whisper
# - yt-dlp, youtube-transcript-api

# Verify installation
python -c "import torch; print(f'PyTorch: {torch.__version__}, CUDA: {torch.cuda.is_available()}')"
python -c "import easyocr; print('easyocr OK')"
```

**Common issues:**
- Running outside a virtual environment → `--setup` will warn you; create a venv first
- Missing system packages → Install `tesseract-ocr` and `ffmpeg` for your OS
- AMD GPU without ROCm → Install ROCm first, then re-run `--setup`

## Configuration Issues

### Issue: API Keys Not Recognized

**Symptoms:**
```
Error: ANTHROPIC_API_KEY not found
401 Unauthorized
```

**Solutions:**

```bash
# Check environment variables
env | grep API_KEY

# Set in current session
export ANTHROPIC_API_KEY=sk-ant-...

# Set permanently (~/.bashrc or ~/.zshrc)
echo 'export ANTHROPIC_API_KEY=sk-ant-...' >> ~/.bashrc
source ~/.bashrc

# Or use .env file
cat > .env <<EOF
ANTHROPIC_API_KEY=sk-ant-...
EOF

# Load .env
set -a
source .env
set +a

# Verify
yonyou-doc2skill config --test
```

### Issue: Configuration File Not Found

**Symptoms:**
```
Error: Config file not found: configs/react.json
FileNotFoundError: [Errno 2] No such file or directory
```

**Solutions:**

```bash
# Check file exists
ls -la configs/react.json

# Use absolute path
yonyou-doc2skill scrape --config /full/path/to/configs/react.json

# Create config directory
mkdir -p ~/.config/yonyou-doc2skill/configs

# Copy config
cp configs/react.json ~/.config/yonyou-doc2skill/configs/

# List available configs
yonyou-doc2skill-config list
```

### Issue: Invalid Configuration Format

**Symptoms:**
```
json.decoder.JSONDecodeError: Expecting value: line 1 column 1
ValidationError: 1 validation error for Config
```

**Solutions:**

```bash
# Validate JSON syntax
python -m json.tool configs/myconfig.json

# Check required fields
yonyou-doc2skill-validate configs/myconfig.json

# Example valid config
cat > configs/test.json <<EOF
{
  "name": "test",
  "base_url": "https://docs.example.com/",
  "selectors": {
    "main_content": "article"
  }
}
EOF
```

## Scraping Issues

### Issue: No Content Extracted

**Symptoms:**
```
Warning: No content found for URL
0 pages scraped
Empty SKILL.md generated
```

**Solutions:**

```bash
# Enable debug mode
export LOG_LEVEL=DEBUG
yonyou-doc2skill scrape --config config.json --verbose

# Test selectors manually
python -c "
from bs4 import BeautifulSoup
import requests
soup = BeautifulSoup(requests.get('URL').content, 'html.parser')
print(soup.select_one('article'))  # Test selector
"

# Adjust selectors in config
{
  "selectors": {
    "main_content": "main",  # Try different selectors
    "title": "h1",
    "code_blocks": "pre"
  }
}

# Use fallback selectors
{
  "selectors": {
    "main_content": ["article", "main", ".content", "#content"]
  }
}
```

### Issue: Scraping Takes Too Long

**Symptoms:**
```
Scraping has been running for 2 hours...
Progress: 50/500 pages (10%)
```

**Solutions:**

```bash
# Enable async scraping (2-3x faster)
yonyou-doc2skill scrape --config config.json --async

# Reduce max pages
yonyou-doc2skill scrape --config config.json --max-pages 100

# Increase concurrency
# Edit config.json:
{
  "concurrency": 20,  # Default: 10
  "rate_limit": 0.2   # Faster (0.2s delay)
}

# Use caching for re-runs
yonyou-doc2skill scrape --config config.json --use-cache
```

### Issue: Pages Not Being Discovered

**Symptoms:**
```
Only 5 pages found
Expected 100+ pages
```

**Solutions:**

```bash
# Check URL patterns
{
  "url_patterns": {
    "include": ["/docs"],  # Make sure this matches
    "exclude": []          # Remove restrictive patterns
  }
}

# Enable breadth-first search
{
  "crawl_strategy": "bfs",  # vs "dfs"
  "max_depth": 10           # Increase depth
}

# Debug URL discovery
yonyou-doc2skill scrape --config config.json --dry-run --verbose
```

## GitHub API Issues

### Issue: Rate Limit Exceeded

**Symptoms:**
```
403 Forbidden
API rate limit exceeded for user
X-RateLimit-Remaining: 0
```

**Solutions:**

```bash
# Check current rate limit
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit

# Use multiple tokens
yonyou-doc2skill config --github
# Follow wizard to add multiple profiles

# Wait for reset
# Check X-RateLimit-Reset header for timestamp

# Use non-interactive mode in CI/CD
yonyou-doc2skill github --repo owner/repo --non-interactive

# Configure rate limit strategy
yonyou-doc2skill config --github
# Choose: prompt / wait / switch / fail
```

### Issue: Invalid GitHub Token

**Symptoms:**
```
401 Unauthorized
Bad credentials
```

**Solutions:**

```bash
# Verify token
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user

# Generate new token
# Visit: https://github.com/settings/tokens
# Scopes needed: repo, read:org

# Update token
yonyou-doc2skill config --github

# Test token
yonyou-doc2skill config --test
```

### Issue: Repository Not Found

**Symptoms:**
```
404 Not Found
Repository not found: owner/repo
```

**Solutions:**

```bash
# Check repository name (case-sensitive)
yonyou-doc2skill github --repo facebook/react  # Correct
yonyou-doc2skill github --repo Facebook/React  # Wrong

# Check if repo is private (requires token)
export GITHUB_TOKEN=ghp_...
yonyou-doc2skill github --repo private/repo

# Verify repo exists
curl https://api.github.com/repos/owner/repo
```

## API & Enhancement Issues

### Issue: Enhancement Fails

**Symptoms:**
```
Error: SKILL.md enhancement failed
AuthenticationError: Invalid API key
```

**Solutions:**

```bash
# Verify API key
yonyou-doc2skill config --test

# Try LOCAL mode (free, uses Claude Code Max)
yonyou-doc2skill enhance output/react/ --mode LOCAL

# Check API key format
# Claude: sk-ant-...
# OpenAI: sk-...
# Gemini: AIza...

# Test API directly
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model":"claude-sonnet-4.5","max_tokens":1024,"messages":[{"role":"user","content":"Hello"}]}'
```

### Issue: Enhancement Hangs/Timeouts

**Symptoms:**
```
Enhancement process not responding
Timeout after 300 seconds
```

**Solutions:**

```bash
# Increase timeout
yonyou-doc2skill enhance output/react/ --timeout 600

# Run in background
yonyou-doc2skill enhance output/react/ --background

# Monitor status
yonyou-doc2skill enhance-status output/react/ --watch

# Kill hung process
ps aux | grep enhance
kill -9 <PID>

# Check system resources
htop
df -h
```

### Issue: API Cost Concerns

**Symptoms:**
```
Worried about API costs for enhancement
Need free alternative
```

**Solutions:**

```bash
# Use LOCAL mode (free!)
yonyou-doc2skill enhance output/react/ --mode LOCAL

# Skip enhancement entirely
yonyou-doc2skill scrape --config config.json --skip-enhance

# Estimate cost before enhancing
# Claude API: ~$0.15-$0.30 per skill
# Check usage: https://console.anthropic.com/

# Use batch processing
for dir in output/*/; do
  yonyou-doc2skill enhance "$dir" --mode LOCAL --background
done
```

## Docker & Kubernetes Issues

### Issue: Container Won't Start

**Symptoms:**
```
Error response from daemon: Container ... is not running
Container exits immediately
```

**Solutions:**

```bash
# Check logs
docker logs yonyoudoc2skill-mcp

# Common issues:
# 1. Missing environment variables
docker run -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY ...

# 2. Port already in use
sudo lsof -i :8765
docker run -p 8766:8765 ...

# 3. Permission issues
docker run --user $(id -u):$(id -g) ...

# Run interactively to debug
docker run -it --entrypoint /bin/bash yonyoudoc2skill:latest
```

### Issue: Kubernetes Pod CrashLoopBackOff

**Symptoms:**
```
NAME                    READY   STATUS             RESTARTS
yonyoudoc2skill-mcp-xxx    0/1     CrashLoopBackOff   5
```

**Solutions:**

```bash
# Check pod logs
kubectl logs -n yonyoudoc2skill yonyoudoc2skill-mcp-xxx

# Describe pod
kubectl describe pod -n yonyoudoc2skill yonyoudoc2skill-mcp-xxx

# Check events
kubectl get events -n yonyoudoc2skill --sort-by='.lastTimestamp'

# Common issues:
# 1. Missing secrets
kubectl get secrets -n yonyoudoc2skill

# 2. Resource constraints
kubectl top nodes
kubectl edit deployment yonyoudoc2skill-mcp -n yonyoudoc2skill

# 3. Liveness probe failing
# Increase initialDelaySeconds in deployment
```

### Issue: Image Pull Errors

**Symptoms:**
```
ErrImagePull
ImagePullBackOff
Failed to pull image
```

**Solutions:**

```bash
# Check image exists
docker pull yonyoudoc2skill:latest

# Create image pull secret
kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=pass \
  -n yonyoudoc2skill

# Add to deployment
spec:
  imagePullSecrets:
  - name: regcred

# Use public image (if available)
image: docker.io/yonyoudoc2skill/yonyoudoc2skill:latest
```

## Performance Issues

### Issue: High Memory Usage

**Symptoms:**
```
Process killed (OOM)
Memory usage: 8GB+
System swapping
```

**Solutions:**

```bash
# Check memory usage
ps aux --sort=-%mem | head -10
htop

# Reduce batch size
yonyou-doc2skill scrape --config config.json --batch-size 10

# Enable memory limits
# Docker:
docker run --memory=4g yonyoudoc2skill:latest

# Kubernetes:
resources:
  limits:
    memory: 4Gi

# Clear cache
rm -rf ~/.cache/yonyou-doc2skill/

# Use streaming for large files
# (automatically handled by library)
```

### Issue: Slow Performance

**Symptoms:**
```
Operations taking much longer than expected
High CPU usage
Disk I/O bottleneck
```

**Solutions:**

```bash
# Enable async operations
yonyou-doc2skill scrape --config config.json --async

# Increase concurrency
{
  "concurrency": 20  # Adjust based on resources
}

# Use SSD for storage
# Move output to SSD:
mv output/ /mnt/ssd/output/

# Monitor performance
# CPU:
mpstat 1
# Disk I/O:
iostat -x 1
# Network:
iftop

# Profile code
python -m cProfile -o profile.stats \
  -m yonyou_doc2skill.cli.doc_scraper --config config.json
```

### Issue: Disk Space Issues

**Symptoms:**
```
No space left on device
Disk full
Cannot create file
```

**Solutions:**

```bash
# Check disk usage
df -h
du -sh output/*

# Clean up old skills
find output/ -type d -mtime +30 -exec rm -rf {} \;

# Compress old benchmarks
tar czf benchmarks-archive.tar.gz benchmarks/
rm -rf benchmarks/*.json

# Use cloud storage
yonyou-doc2skill scrape --config config.json \
  --storage s3 \
  --bucket my-skills-bucket

# Clear cache
yonyou-doc2skill cache --clear
```

## Storage Issues

### Issue: S3 Upload Fails

**Symptoms:**
```
botocore.exceptions.NoCredentialsError
AccessDenied
```

**Solutions:**

```bash
# Check credentials
aws sts get-caller-identity

# Configure AWS CLI
aws configure

# Set environment variables
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-east-1

# Check bucket permissions
aws s3 ls s3://my-bucket/

# Test upload
echo "test" > test.txt
aws s3 cp test.txt s3://my-bucket/
```

### Issue: GCS Authentication Failed

**Symptoms:**
```
google.auth.exceptions.DefaultCredentialsError
Permission denied
```

**Solutions:**

```bash
# Set credentials file
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json

# Or use gcloud auth
gcloud auth application-default login

# Verify permissions
gsutil ls gs://my-bucket/

# Test upload
echo "test" > test.txt
gsutil cp test.txt gs://my-bucket/
```

## Network Issues

### Issue: Connection Timeouts

**Symptoms:**
```
requests.exceptions.ConnectionError
ReadTimeout
Connection refused
```

**Solutions:**

```bash
# Check network connectivity
ping google.com
curl https://docs.example.com/

# Increase timeout
{
  "timeout": 60  # seconds
}

# Use proxy if behind firewall
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080

# Check DNS resolution
nslookup docs.example.com
dig docs.example.com

# Test with curl
curl -v https://docs.example.com/
```

### Issue: SSL/TLS Errors

**Symptoms:**
```
ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
SSLCertVerificationError
```

**Solutions:**

```bash
# Update certificates
# Ubuntu/Debian:
sudo apt update && sudo apt install --reinstall ca-certificates

# RHEL/CentOS:
sudo yum reinstall ca-certificates

# As last resort (not recommended for production):
export PYTHONHTTPSVERIFY=0
# Or in code:
yonyou-doc2skill scrape --config config.json --no-verify-ssl
```

## General Debug Techniques

### Enable Debug Logging

```bash
# Set debug level
export LOG_LEVEL=DEBUG

# Run with verbose output
yonyou-doc2skill scrape --config config.json --verbose

# Save logs to file
yonyou-doc2skill scrape --config config.json 2>&1 | tee debug.log
```

### Collect Diagnostic Information

```bash
# System info
uname -a
python --version
pip --version

# Package info
pip show yonyou-doc2skill
pip list | grep skill

# Environment
env | grep -E '(API_KEY|TOKEN|PATH)'

# Recent errors
grep -i error /var/log/yonyoudoc2skill/*.log | tail -20

# Package all diagnostics
tar czf diagnostics.tar.gz \
  debug.log \
  ~/.config/yonyou-doc2skill/ \
  /var/log/yonyoudoc2skill/
```

### Test Individual Components

```bash
# Test scraper
python -c "
from yonyou_doc2skill.cli.doc_scraper import scrape_all
pages = scrape_all('configs/test.json')
print(f'Scraped {len(pages)} pages')
"

# Test GitHub API
python -c "
from yonyou_doc2skill.cli.github_fetcher import GitHubFetcher
fetcher = GitHubFetcher()
repo = fetcher.fetch('facebook/react')
print(repo['full_name'])
"

# Test embeddings
python -c "
from yonyou_doc2skill.embedding.generator import EmbeddingGenerator
gen = EmbeddingGenerator()
emb = gen.generate('test', model='text-embedding-3-small')
print(f'Embedding dimension: {len(emb)}')
"
```

### Interactive Debugging

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use ipdb
import ipdb; ipdb.set_trace()

# Debug with IPython
ipython -i script.py
```

## Getting More Help

If you're still experiencing issues:

1. **Search existing issues:** https://github.com/yonyou/yonyou-doc2skill/issues
2. **Check documentation:** https://docs.yonyou.example/yonyou-doc2skill/
3. **Ask on GitHub Discussions:** https://github.com/yonyou/yonyou-doc2skill/discussions
4. **Open a new issue:** Include:
   - Yonyou Doc2Skill version (`yonyou-doc2skill --version`)
   - Python version (`python --version`)
   - Operating system
   - Complete error message
   - Steps to reproduce
   - Diagnostic information (see above)

## Source-Type-Specific Issues

### Issue: Missing Optional Dependencies for New Source Types

**Symptoms:**
```
ModuleNotFoundError: No module named 'ebooklib'
ModuleNotFoundError: No module named 'python-docx'
ModuleNotFoundError: No module named 'python-pptx'
ImportError: Missing dependency for jupyter extraction
```

**Solutions:**

```bash
# Install all optional dependencies at once
pip install yonyou-doc2skill[all]

# Or install per source type
pip install python-docx          # Word (.docx) support
pip install ebooklib              # EPUB support
pip install python-pptx           # PowerPoint (.pptx) support
pip install nbformat nbconvert    # Jupyter Notebook support
pip install pyyaml jsonschema     # OpenAPI/Swagger support
pip install asciidoctor           # AsciiDoc support (or install system asciidoctor)
pip install feedparser            # RSS/Atom feed support
pip install groff                 # Man page support (system package)

# Video support (GPU-aware)
yonyou-doc2skill video --setup
```

### Issue: Confluence API Authentication Fails

**Symptoms:**
```
401 Unauthorized: Confluence API rejected credentials
Error: CONFLUENCE_TOKEN not found
```

**Solutions:**

```bash
# Set Confluence Cloud credentials
export CONFLUENCE_URL=https://yourorg.atlassian.net
export CONFLUENCE_EMAIL=your-email@example.com
export CONFLUENCE_TOKEN=your-api-token

# Generate API token at:
# https://id.atlassian.com/manage-profile/security/api-tokens

# Test connection
yonyou-doc2skill confluence --space MYSPACE --dry-run

# For Confluence Server/Data Center, use personal access token:
export CONFLUENCE_TOKEN=your-pat
```

### Issue: Notion API Authentication Fails

**Symptoms:**
```
401 Unauthorized: Notion API rejected credentials
Error: NOTION_TOKEN not found
```

**Solutions:**

```bash
# Set Notion integration token
export NOTION_TOKEN=secret_...

# Create an integration at:
# https://www.notion.so/my-integrations

# IMPORTANT: Share the target database/page with your integration
# (click "..." menu on page → "Add connections" → select your integration)

# Test connection
yonyou-doc2skill notion --database DATABASE_ID --dry-run
```

### Issue: Jupyter Notebook Extraction Fails

**Symptoms:**
```
Error: Cannot read notebook format
nbformat.reader.NotJSONError
```

**Solutions:**

```bash
# Ensure notebook is valid JSON
python -c "import json; json.load(open('notebook.ipynb'))"

# Install required deps
pip install nbformat nbconvert

# Try with explicit format version
yonyou-doc2skill jupyter notebook.ipynb --nbformat 4
```

### Issue: OpenAPI Spec Parsing Fails

**Symptoms:**
```
Error: Not a valid OpenAPI specification
Error: Missing 'openapi' or 'swagger' field
```

**Solutions:**

```bash
# Validate your spec first
pip install openapi-spec-validator
python -c "
from openapi_spec_validator import validate
validate({'openapi': '3.0.0', ...})
"

# Ensure the file has the 'openapi' or 'swagger' top-level key
# Supported: OpenAPI 3.x and Swagger 2.0

# For remote specs
yonyou-doc2skill openapi https://api.example.com/openapi.json --name my-api
```

### Issue: EPUB Extraction Produces Empty Output

**Symptoms:**
```
Warning: No content found in EPUB
0 chapters extracted
```

**Solutions:**

```bash
# Check EPUB is valid
pip install epubcheck
epubcheck book.epub

# Try with different content extraction
yonyou-doc2skill epub book.epub --extract-images --verbose

# Some DRM-protected EPUBs cannot be extracted
# Ensure your EPUB is DRM-free
```

### Issue: Slack/Discord Export Not Recognized

**Symptoms:**
```
Error: Cannot detect chat platform from export directory
Error: No messages found in export
```

**Solutions:**

```bash
# Specify platform explicitly
yonyou-doc2skill chat --platform slack --export-dir ./slack-export
yonyou-doc2skill chat --platform discord --export-dir ./discord-export

# For Slack: Export from Workspace Settings → Import/Export
# For Discord: Use DiscordChatExporter or similar tool

# Check export directory structure
ls ./slack-export/
# Should contain: channels/, users.json, etc.
```

---

## Common Error Messages Reference

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError` | Package not installed | `pip install yonyou-doc2skill` |
| `401 Unauthorized` | Invalid API key | Check API key format |
| `403 Forbidden` | Rate limit exceeded | Add more GitHub tokens |
| `404 Not Found` | Invalid URL/repo | Verify URL is correct |
| `429 Too Many Requests` | API rate limit | Wait or use multiple keys |
| `ConnectionError` | Network issue | Check internet connection |
| `TimeoutError` | Request too slow | Increase timeout |
| `MemoryError` | Out of memory | Reduce batch size |
| `PermissionError` | Access denied | Check file permissions |
| `FileNotFoundError` | Missing file | Verify file path |
| `No module named 'ebooklib'` | EPUB dep missing | `pip install ebooklib` |
| `No module named 'python-docx'` | Word dep missing | `pip install python-docx` |
| `No module named 'python-pptx'` | PPTX dep missing | `pip install python-pptx` |
| `CONFLUENCE_TOKEN not found` | Confluence auth missing | Set env vars (see above) |
| `NOTION_TOKEN not found` | Notion auth missing | Set env vars (see above) |

---

**Still stuck?** Open an issue with the "help wanted" label and we'll assist you!
