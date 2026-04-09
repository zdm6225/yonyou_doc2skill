# Installation Guide

> **Yonyou Doc2Skill v3.2.0**

Get Yonyou Doc2Skill installed and running in under 5 minutes.

---

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **Python** | 3.10 | 3.11 or 3.12 |
| **RAM** | 4 GB | 8 GB+ |
| **Disk** | 500 MB | 2 GB+ |
| **OS** | Linux, macOS, Windows (WSL) | Linux, macOS |

---

## Quick Install

### Option 1: pip (Recommended)

```bash
# Basic installation
pip install yonyou-doc2skill

# With all platform support
pip install yonyou-doc2skill[all-llms]

# Verify installation
yonyou-doc2skill --version
```

### Option 2: pipx (Isolated)

```bash
# Install pipx if not available
pip install pipx
pipx ensurepath

# Install yonyou-doc2skill
pipx install yonyou-doc2skill[all-llms]
```

### Option 3: Development (from source)

```bash
# Clone repository
git clone https://github.com/yonyou/yonyou-doc2skill.git
cd yonyou_doc2skill

# Install in editable mode
pip install -e ".[all-llms,dev]"

# Verify
yonyou-doc2skill --version
```

---

## Installation Options

### Minimal Install

Just the core functionality:

```bash
pip install yonyou-doc2skill
```

**Includes:**
- Documentation scraping
- Basic packaging
- Local enhancement (Claude Code)

### Full Install

All features and platforms:

```bash
pip install yonyou-doc2skill[all-llms]
```

**Includes:**
- Claude AI support
- Google Gemini support
- OpenAI ChatGPT support
- MiniMax AI support
- All vector databases
- MCP server
- Cloud storage (S3, GCS, Azure)

### Custom Install

Install only what you need:

```bash
# Specific platform only
pip install yonyou-doc2skill[gemini]      # Google Gemini
pip install yonyou-doc2skill[openai]      # OpenAI
pip install yonyou-doc2skill[minimax]     # MiniMax AI
pip install yonyou-doc2skill[chroma]      # ChromaDB

# Multiple extras
pip install yonyou-doc2skill[gemini,openai,chroma]

# Development
pip install yonyou-doc2skill[dev]
```

---

## Available Extras

| Extra | Description | Install Command |
|-------|-------------|-----------------|
| `gemini` | Google Gemini support | `pip install yonyou-doc2skill[gemini]` |
| `openai` | OpenAI ChatGPT support | `pip install yonyou-doc2skill[openai]` |
| `minimax` | MiniMax AI support | `pip install yonyou-doc2skill[minimax]` |
| `mcp` | MCP server | `pip install yonyou-doc2skill[mcp]` |
| `chroma` | ChromaDB export | `pip install yonyou-doc2skill[chroma]` |
| `weaviate` | Weaviate export | `pip install yonyou-doc2skill[weaviate]` |
| `qdrant` | Qdrant export | `pip install yonyou-doc2skill[qdrant]` |
| `faiss` | FAISS export | `pip install yonyou-doc2skill[faiss]` |
| `s3` | AWS S3 storage | `pip install yonyou-doc2skill[s3]` |
| `gcs` | Google Cloud Storage | `pip install yonyou-doc2skill[gcs]` |
| `azure` | Azure Blob Storage | `pip install yonyou-doc2skill[azure]` |
| `embedding` | Embedding server | `pip install yonyou-doc2skill[embedding]` |
| `video` | YouTube/video transcript extraction | `pip install yonyou-doc2skill[video]` |
| `video-full` | + Whisper transcription, scene detection | `pip install yonyou-doc2skill[video-full]` |
| `jupyter` | Jupyter Notebook extraction | `pip install yonyou-doc2skill[jupyter]` |
| `asciidoc` | AsciiDoc document processing | `pip install yonyou-doc2skill[asciidoc]` |
| `pptx` | PowerPoint presentation extraction | `pip install yonyou-doc2skill[pptx]` |
| `rss` | RSS/Atom feed extraction | `pip install yonyou-doc2skill[rss]` |
| `confluence` | Confluence wiki extraction | `pip install yonyou-doc2skill[confluence]` |
| `notion` | Notion workspace extraction | `pip install yonyou-doc2skill[notion]` |
| `chat` | Slack/Discord export extraction | `pip install yonyou-doc2skill[chat]` |
| `all-llms` | All LLM platforms | `pip install yonyou-doc2skill[all-llms]` |
| `all` | Everything | `pip install yonyou-doc2skill[all]` |
| `dev` | Development tools | `pip install yonyou-doc2skill[dev]` |

> **Video visual deps:** After installing `yonyou-doc2skill[video-full]`, run `yonyou-doc2skill video --setup` to auto-detect your GPU (NVIDIA/AMD/CPU) and install the correct PyTorch variant + easyocr.

---

## Post-Installation Setup

### 1. Configure API Keys (Optional)

For AI enhancement and uploads:

```bash
# Interactive configuration wizard
yonyou-doc2skill config

# Or set environment variables
export ANTHROPIC_API_KEY=sk-ant-...
export GITHUB_TOKEN=ghp_...
```

### 2. Verify Installation

```bash
# Check version
yonyou-doc2skill --version

# See all commands
yonyou-doc2skill --help

# Test configuration
yonyou-doc2skill config --test
```

### 3. Quick Test

```bash
# List available presets
yonyou-doc2skill estimate --all

# Do a dry run
yonyou-doc2skill create https://docs.python.org/3/ --dry-run
```

---

## Platform-Specific Notes

### macOS

```bash
# Using Homebrew Python
brew install python@3.12
pip3.12 install yonyou-doc2skill[all-llms]

# Or with pyenv
pyenv install 3.12
pyenv global 3.12
pip install yonyou-doc2skill[all-llms]
```

### Linux (Ubuntu/Debian)

```bash
# Install Python and pip
sudo apt update
sudo apt install python3-pip python3-venv

# Install yonyou-doc2skill
pip3 install yonyou-doc2skill[all-llms]

# Make available system-wide
sudo ln -s ~/.local/bin/yonyou-doc2skill /usr/local/bin/
```

### Windows

**Recommended:** Use WSL2

```powershell
# Or use Windows directly (PowerShell)
python -m pip install yonyou-doc2skill[all-llms]

# Add to PATH if needed
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:APPDATA\Python\Python312\Scripts", "User")
```

### Docker

```bash
# Pull image
docker pull yonyoudoc2skill/yonyou-doc2skill:latest

# Run
docker run -it --rm \
  -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
  -v $(pwd)/output:/output \
  yonyoudoc2skill/yonyou-doc2skill \
  yonyou-doc2skill create https://docs.react.dev/
```

---

## Troubleshooting

### "command not found: yonyou-doc2skill"

```bash
# Add pip bin to PATH
export PATH="$HOME/.local/bin:$PATH"

# Or reinstall with --user
pip install --user --force-reinstall yonyou-doc2skill
```

### Permission denied

```bash
# Don't use sudo with pip
# Instead:
pip install --user yonyou-doc2skill

# Or use a virtual environment
python3 -m venv venv
source venv/bin/activate
pip install yonyou-doc2skill[all-llms]
```

### Import errors

```bash
# For development installs, ensure editable mode
pip install -e .

# Check installation
python -c "import yonyou_doc2skill; print(yonyou_doc2skill.__version__)"
```

### Version conflicts

```bash
# Use virtual environment
python3 -m venv yonyou-doc2skill-env
source yonyou-doc2skill-env/bin/activate
pip install yonyou-doc2skill[all-llms]
```

---

## Upgrade

```bash
# Upgrade to latest
pip install --upgrade yonyou-doc2skill

# Upgrade with all extras
pip install --upgrade yonyou-doc2skill[all-llms]

# Check current version
yonyou-doc2skill --version

# See what's new
pip show yonyou-doc2skill
```

---

## Uninstall

```bash
pip uninstall yonyou-doc2skill

# Clean up config (optional)
rm -rf ~/.config/yonyou-doc2skill/
rm -rf ~/.cache/yonyou-doc2skill/
```

---

## Next Steps

- [Quick Start Guide](02-quick-start.md) - Create your first skill in 3 commands
- [Your First Skill](03-your-first-skill.md) - Complete walkthrough

---

## Getting Help

```bash
# Command help
yonyou-doc2skill --help
yonyou-doc2skill create --help

# Documentation
# https://github.com/yonyou/yonyou-doc2skill/tree/main/docs

# Issues
# https://github.com/yonyou/yonyou-doc2skill/issues
```
