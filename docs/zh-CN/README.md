# Yonyou Doc2Skill Documentation

> **Complete documentation for Yonyou Doc2Skill v3.4.0**

---

## Welcome!

This is the official documentation for **Yonyou Doc2Skill** - the universal tool for converting 17 source types (documentation, code, PDFs, videos, notebooks, wikis, and more) into AI-ready skills.

---

## Where Should I Start?

### 🚀 I'm New Here

Start with our **Getting Started** guides:

1. [Installation](getting-started/01-installation.md) - Install Yonyou Doc2Skill
2. [Quick Start](getting-started/02-quick-start.md) - Create your first skill in 3 commands
3. [Your First Skill](getting-started/03-your-first-skill.md) - Complete walkthrough
4. [Next Steps](getting-started/04-next-steps.md) - Where to go from here

### 📖 I Want to Learn

Explore our **User Guides**:

- [Core Concepts](user-guide/01-core-concepts.md) - How Yonyou Doc2Skill works
- [Scraping Guide](user-guide/02-scraping.md) - All scraping options
- [Enhancement Guide](user-guide/03-enhancement.md) - AI enhancement explained
- [Packaging Guide](user-guide/04-packaging.md) - Export to platforms
- [Workflows Guide](user-guide/05-workflows.md) - Enhancement workflows
- [Troubleshooting](user-guide/06-troubleshooting.md) - Common issues

### 📚 I Need Reference

Look up specific information:

- [CLI Reference](reference/CLI_REFERENCE.md) - All 30+ commands
- [MCP Reference](reference/MCP_REFERENCE.md) - 27 MCP tools
- [Feature Matrix](reference/FEATURE_MATRIX.md) - 17 source types × 12 platforms
- [Config Format](reference/CONFIG_FORMAT.md) - JSON specification
- [Environment Variables](reference/ENVIRONMENT_VARIABLES.md) - All env vars

### 🚀 I'm Ready for Advanced Topics

Power user features:

- [MCP Server Setup](advanced/mcp-server.md) - MCP integration
- [MCP Tools Deep Dive](advanced/mcp-tools.md) - Advanced MCP usage
- [Custom Workflows](advanced/custom-workflows.md) - Create workflows
- [Multi-Source Scraping](advanced/multi-source.md) - Combine sources

---

## Quick Reference

### The 3 Commands

```bash
# 1. Install
pip install yonyou-doc2skill

# 2. Create skill from any of 17 source types
yonyou-doc2skill create https://docs.django.com/

# 3. Package for Claude
yonyou-doc2skill package output/django --target claude
```

### Common Commands

```bash
# Scrape documentation
yonyou-doc2skill scrape --config react

# Analyze GitHub repo
yonyou-doc2skill github --repo facebook/react

# Extract PDF
yonyou-doc2skill pdf manual.pdf --name docs

# Analyze local code
yonyou-doc2skill analyze --directory ./my-project

# New source types (v3.2.0)
yonyou-doc2skill create notebook.ipynb              # Jupyter Notebook
yonyou-doc2skill create page.html                   # Local HTML
yonyou-doc2skill create api-spec.yaml               # OpenAPI/Swagger
yonyou-doc2skill create guide.adoc                  # AsciiDoc
yonyou-doc2skill create slides.pptx                 # PowerPoint
yonyou-doc2skill rss --feed-url https://blog.example.com/feed  # RSS/Atom
yonyou-doc2skill manpage --man-path curl.1           # Man pages
yonyou-doc2skill confluence --space-key DEV          # Confluence
yonyou-doc2skill notion --database-id abc123         # Notion
yonyou-doc2skill chat --export-path ./slack-export/  # Slack/Discord

# Enhance skill
yonyou-doc2skill enhance output/my-skill/

# Package for platform
yonyou-doc2skill package output/my-skill/ --target claude

# Upload
yonyou-doc2skill upload output/my-skill-claude.zip

# List workflows
yonyou-doc2skill workflows list
```

---

## Documentation Structure

```
docs/
├── README.md                 # This file - start here
├── ARCHITECTURE.md          # How docs are organized
│
├── getting-started/         # For new users
│   ├── 01-installation.md
│   ├── 02-quick-start.md
│   ├── 03-your-first-skill.md
│   └── 04-next-steps.md
│
├── user-guide/              # Common tasks
│   ├── 01-core-concepts.md
│   ├── 02-scraping.md
│   ├── 03-enhancement.md
│   ├── 04-packaging.md
│   ├── 05-workflows.md
│   └── 06-troubleshooting.md
│
├── reference/               # Technical reference
│   ├── CLI_REFERENCE.md     # 30+ commands
│   ├── MCP_REFERENCE.md     # 27 MCP tools
│   ├── CONFIG_FORMAT.md     # JSON spec
│   └── ENVIRONMENT_VARIABLES.md
│
└── advanced/                # Power user topics
    ├── mcp-server.md
    ├── mcp-tools.md
    ├── custom-workflows.md
    └── multi-source.md
```

---

## By Use Case

### I Want to Build AI Skills

For Claude, Gemini, ChatGPT:

1. [Quick Start](getting-started/02-quick-start.md)
2. [Enhancement Guide](user-guide/03-enhancement.md)
3. [Workflows Guide](user-guide/05-workflows.md)

### I Want to Build RAG Pipelines

For LangChain, LlamaIndex, vector DBs:

1. [Core Concepts](user-guide/01-core-concepts.md)
2. [Packaging Guide](user-guide/04-packaging.md)
3. [MCP Reference](reference/MCP_REFERENCE.md)

### I Want AI Coding Assistance

For Cursor, Windsurf, Cline:

1. [Your First Skill](getting-started/03-your-first-skill.md)
2. [Local Codebase Analysis](user-guide/02-scraping.md#local-codebase-analysis)
3. `yonyou-doc2skill install-agent --agent cursor`

---

## Version Information

- **Current Version:** 3.4.0
- **Last Updated:** 2026-03-21
- **Python Required:** 3.10+

---

## Contributing to Documentation

Found an issue? Want to improve docs?

1. Edit files in the `docs/` directory
2. Follow the existing structure
3. Submit a PR

See [Contributing Guide](../CONTRIBUTING.md) for details.

---

## External Links

- **Main Repository:** https://github.com/yonyou/yonyou-doc2skill
- **Website:** https://docs.yonyou.example/yonyou-doc2skill/
- **PyPI:** https://pypi.org/project/yonyou-doc2skill/
- **Issues:** https://github.com/yonyou/yonyou-doc2skill/issues

---

## License

MIT License - see [LICENSE](../LICENSE) file.

---

*Happy skill building! 🚀*
