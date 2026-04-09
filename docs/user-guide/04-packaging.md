# Packaging Guide

> **Yonyou Doc2Skill v3.2.0**  
> **Export skills to AI platforms and vector databases**

---

## Overview

Packaging converts your skill directory into a platform-specific format:

```
output/my-skill/ ──▶ Packager ──▶ output/my-skill-{platform}.{format}
    ↓                                ↓
(SKILL.md +        Platform-specific  (ZIP, tar.gz,
 references)        formatting        directories,
                                     FAISS index)
```

---

## Supported Platforms

| Platform | Format | Extension | Best For |
|----------|--------|-----------|----------|
| **Claude AI** | ZIP + YAML | `.zip` | Claude Code, Claude API |
| **Google Gemini** | tar.gz | `.tar.gz` | Gemini skills |
| **OpenAI ChatGPT** | ZIP + Vector | `.zip` | Custom GPTs |
| **MiniMax** | ZIP | `.zip` | MiniMax platform |
| **OpenCode** | ZIP | `.zip` | OpenCode platform |
| **Kimi** | ZIP | `.zip` | Kimi platform |
| **DeepSeek** | ZIP | `.zip` | DeepSeek platform |
| **Qwen** | ZIP | `.zip` | Qwen platform |
| **OpenRouter** | ZIP | `.zip` | Multi-model routing |
| **Together AI** | ZIP | `.zip` | Open-source models |
| **Fireworks AI** | ZIP | `.zip` | Fast inference |
| **LangChain** | Documents | directory | RAG pipelines |
| **LlamaIndex** | TextNodes | directory | Query engines |
| **Haystack** | Documents | directory | Enterprise RAG |
| **Pinecone** | Markdown | `.zip` | Vector upsert |
| **ChromaDB** | Collection | `.zip` | Local vector DB |
| **Weaviate** | Objects | `.zip` | Vector database |
| **Qdrant** | Points | `.zip` | Vector database |
| **FAISS** | Index | `.faiss` | Local similarity |
| **Markdown** | ZIP | `.zip` | Universal export |
| **Cursor** | .cursorrules | file | IDE AI context |
| **Windsurf** | .windsurfrules | file | IDE AI context |
| **Cline** | .clinerules | file | VS Code AI |
| **Roo** | .roorules | file | VS Code AI |
| **Aider** | .aider | file | Terminal AI coding |
| **Bolt** | bolt context | file | Web IDE AI |
| **Kilo** | kilo context | file | IDE AI context |
| **Continue** | .continue | file | IDE AI context |
| **Kimi Code** | kimi context | file | IDE AI context |

---

## Basic Packaging

### Package for Claude (Default)

```bash
# Default packaging
yonyou-doc2skill package output/my-skill/

# Explicit target
yonyou-doc2skill package output/my-skill/ --target claude

# Output: output/my-skill-claude.zip
```

### Package for Other Platforms

```bash
# Google Gemini
yonyou-doc2skill package output/my-skill/ --target gemini
# Output: output/my-skill-gemini.tar.gz

# OpenAI
yonyou-doc2skill package output/my-skill/ --target openai
# Output: output/my-skill-openai.zip

# LangChain
yonyou-doc2skill package output/my-skill/ --target langchain
# Output: output/my-skill-langchain/ directory

# ChromaDB
yonyou-doc2skill package output/my-skill/ --target chroma
# Output: output/my-skill-chroma.zip
```

---

## Multi-Platform Packaging

### Package for All Platforms

```bash
# Create skill once
yonyou-doc2skill create <source>

# Package for multiple platforms
for platform in claude gemini openai langchain; do
  echo "Packaging for $platform..."
  yonyou-doc2skill package output/my-skill/ --target $platform
done

# Results:
# output/my-skill-claude.zip
# output/my-skill-gemini.tar.gz
# output/my-skill-openai.zip
# output/my-skill-langchain/
```

### Batch Packaging Script

```bash
#!/bin/bash
SKILL_DIR="output/my-skill"
PLATFORMS="claude gemini openai langchain llama-index chroma"

for platform in $PLATFORMS; do
  echo "▶️ Packaging for $platform..."
  yonyou-doc2skill package "$SKILL_DIR" --target "$platform"
  
  if [ $? -eq 0 ]; then
    echo "✅ $platform done"
  else
    echo "❌ $platform failed"
 fi
done

echo "🎉 All platforms packaged!"
```

---

## Packaging Options

### Skip Quality Check

```bash
# Skip validation (faster)
yonyou-doc2skill package output/my-skill/ --skip-quality-check
```

### Don't Open Output Folder

```bash
# Prevent opening folder after packaging
yonyou-doc2skill package output/my-skill/ --no-open
```

### Auto-Upload After Packaging

```bash
# Package and upload
export ANTHROPIC_API_KEY=sk-ant-...
yonyou-doc2skill package output/my-skill/ --target claude --upload
```

---

## Streaming Mode

For very large skills, use streaming to reduce memory usage:

```bash
# Enable streaming
yonyou-doc2skill package output/large-skill/ --streaming

# Custom chunk size
yonyou-doc2skill package output/large-skill/ \
  --streaming \
  --streaming-chunk-chars 2000 \
  --streaming-overlap-chars 100
```

**When to use:**
- Skills > 500 pages
- Limited RAM (< 8GB)
- Batch processing many skills

---

## RAG Chunking

Optimize for Retrieval-Augmented Generation:

```bash
# Enable semantic chunking
yonyou-doc2skill package output/my-skill/ \
  --target langchain \
  --chunk-for-rag \
  --chunk-tokens 512

# Custom chunk size
yonyou-doc2skill package output/my-skill/ \
  --target chroma \
  --chunk-tokens 256 \
  --chunk-overlap-tokens 50
```

**Chunking Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--chunk-for-rag` | auto | Enable chunking |
| `--chunk-tokens` | 512 | Tokens per chunk |
| `--chunk-overlap-tokens` | 50 | Overlap between chunks (tokens) |
| `--no-preserve-code-blocks` | - | Allow splitting code blocks |

> **Auto-scaling overlap:** When `--chunk-tokens` is set to a non-default value but `--chunk-overlap-tokens` is left at default (50), the overlap automatically scales to `max(50, chunk_tokens / 10)` for better context preservation with larger chunks.

---

## Platform-Specific Details

### Claude AI

```bash
yonyou-doc2skill package output/my-skill/ --target claude
```

**Upload:**
```bash
# Auto-upload
yonyou-doc2skill package output/my-skill/ --target claude --upload

# Manual upload
yonyou-doc2skill upload output/my-skill-claude.zip --target claude
```

**Format:**
- ZIP archive
- Contains SKILL.md + references/
- Includes YAML manifest

---

### Google Gemini

```bash
yonyou-doc2skill package output/my-skill/ --target gemini
```

**Upload:**
```bash
export GOOGLE_API_KEY=AIza...
yonyou-doc2skill upload output/my-skill-gemini.tar.gz --target gemini
```

**Format:**
- tar.gz archive
- Optimized for Gemini's format

---

### OpenAI ChatGPT

```bash
yonyou-doc2skill package output/my-skill/ --target openai
```

**Upload:**
```bash
export OPENAI_API_KEY=sk-...
yonyou-doc2skill upload output/my-skill-openai.zip --target openai
```

**Format:**
- ZIP with vector embeddings
- Ready for Assistants API

---

### LangChain

```bash
yonyou-doc2skill package output/my-skill/ --target langchain
```

**Usage:**
```python
from langchain.document_loaders import DirectoryLoader

loader = DirectoryLoader("output/my-skill-langchain/")
docs = loader.load()

# Use in RAG pipeline
```

**Format:**
- Directory of Document objects
- JSON metadata

---

### ChromaDB

```bash
yonyou-doc2skill package output/my-skill/ --target chroma
```

**Upload:**
```bash
# Local ChromaDB
yonyou-doc2skill upload output/my-skill-chroma.zip --target chroma

# With custom URL
yonyou-doc2skill upload output/my-skill-chroma.zip \
  --target chroma \
  --chroma-url http://localhost:8000
```

**Usage:**
```python
import chromadb

client = chromadb.HttpClient(host="localhost", port=8000)
collection = client.get_collection("my-skill")
```

---

### Weaviate

```bash
yonyou-doc2skill package output/my-skill/ --target weaviate
```

**Upload:**
```bash
# Local Weaviate
yonyou-doc2skill upload output/my-skill-weaviate.zip --target weaviate

# Weaviate Cloud
yonyou-doc2skill upload output/my-skill-weaviate.zip \
  --target weaviate \
  --use-cloud \
  --cluster-url https://xxx.weaviate.network
```

---

### Cursor IDE

```bash
# Package (actually creates .cursorrules file)
yonyou-doc2skill package output/my-skill/ --target cursor

# Or install directly
yonyou-doc2skill install-agent output/my-skill/ --agent cursor
```

**Result:** `.cursorrules` file in your project root.

---

### Windsurf IDE

```bash
yonyou-doc2skill install-agent output/my-skill/ --agent windsurf
```

**Result:** `.windsurfrules` file in your project root.

---

## Quality Check

Before packaging, skills are validated:

```bash
# Check quality
yonyou-doc2skill quality output/my-skill/

# Detailed report
yonyou-doc2skill quality output/my-skill/ --report

# Set minimum threshold
yonyou-doc2skill quality output/my-skill/ --threshold 7.0
```

**Quality Metrics:**
- SKILL.md completeness
- Code example coverage
- Navigation structure
- Reference file organization

---

## Output Structure

### After Packaging

```
output/
├── my-skill/                    # Source skill
│   ├── SKILL.md
│   └── references/
│
├── my-skill-claude.zip          # Claude package
├── my-skill-gemini.tar.gz       # Gemini package
├── my-skill-openai.zip          # OpenAI package
├── my-skill-langchain/          # LangChain directory
├── my-skill-chroma.zip          # ChromaDB package
└── my-skill-weaviate.zip        # Weaviate package
```

---

## Troubleshooting

### "Package validation failed"

**Problem:** SKILL.md is missing or malformed

**Solution:**
```bash
# Check skill structure
ls output/my-skill/

# Rebuild if needed
yonyou-doc2skill create --config my-config --skip-scrape

# Or recreate
yonyou-doc2skill create <source>
```

### "Target platform not supported"

**Problem:** Typo in target name

**Solution:**
```bash
# Check available targets
yonyou-doc2skill package --help

# Common targets: claude, gemini, openai, langchain, chroma, weaviate
```

### "Upload failed"

**Problem:** Missing API key

**Solution:**
```bash
# Set API key
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=AIza...
export OPENAI_API_KEY=sk-...

# Try again
yonyou-doc2skill upload output/my-skill-claude.zip --target claude
```

### "Out of memory"

**Problem:** Skill too large for memory

**Solution:**
```bash
# Use streaming mode
yonyou-doc2skill package output/my-skill/ --streaming

# Smaller chunks
yonyou-doc2skill package output/my-skill/ --streaming --streaming-chunk-chars 1000
```

---

## Best Practices

### 1. Package Once, Use Everywhere

```bash
# Create once
yonyou-doc2skill create <source>

# Package for all needed platforms
for platform in claude gemini langchain; do
  yonyou-doc2skill package output/my-skill/ --target $platform
done
```

### 2. Check Quality Before Packaging

```bash
# Validate first
yonyou-doc2skill quality output/my-skill/ --threshold 6.0

# Then package
yonyou-doc2skill package output/my-skill/
```

### 3. Use Streaming for Large Skills

```bash
# Automatically detected, but can force
yonyou-doc2skill package output/large-skill/ --streaming
```

### 4. Keep Original Skill Directory

Don't delete `output/my-skill/` after packaging - you might want to:
- Re-package for other platforms
- Apply different workflows
- Update and re-enhance

---

## Next Steps

- [Workflows Guide](05-workflows.md) - Apply workflows before packaging
- [MCP Reference](../reference/MCP_REFERENCE.md) - Package via MCP
- [Vector DB Integrations](../integrations/) - Platform-specific guides
