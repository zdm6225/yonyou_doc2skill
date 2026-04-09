# Yonyou Doc2Skill — Claude Code Plugin

Transform 17 source types into AI-ready skills and RAG knowledge, directly from Claude Code.

## Installation

### From the Official Plugin Directory

```
/plugin install yonyou-doc2skill@claude-plugin-directory
```

Or browse for it in `/plugin > Discover`.

### Local Installation (for development)

```bash
claude --plugin-dir ./path/to/yonyou-doc2skill-plugin
```

### Prerequisites

The plugin requires `yonyou-doc2skill` to be installed:

```bash
pip install yonyou-doc2skill[mcp]
```

## What's Included

### MCP Server (35 tools)

The plugin bundles the Yonyou Doc2Skill MCP server providing tools for:
- Scraping documentation, GitHub repos, PDFs, videos, and 13 other source types
- Packaging skills for 16+ LLM platforms
- Exporting to vector databases (Weaviate, Chroma, FAISS, Qdrant)
- Managing configs, workflows, and sources

### Slash Commands

| Command | Description |
|---------|-------------|
| `/yonyou-doc2skill:create-skill <source>` | Create a skill from any source (auto-detects type) |
| `/yonyou-doc2skill:sync-config <config>` | Sync config URLs against live docs |
| `/yonyou-doc2skill:install-skill <source>` | End-to-end: fetch, scrape, enhance, package, install |

### Agent Skill

The **skill-builder** skill is automatically available to Claude. It detects source types and uses the appropriate MCP tools to build skills autonomously.

## Usage Examples

```
# Create a skill from a documentation site
/yonyou-doc2skill:create-skill https://react.dev

# Create from a GitHub repo, targeting LangChain
/yonyou-doc2skill:create-skill pallets/flask --target langchain

# Full install workflow with AI enhancement
/yonyou-doc2skill:install-skill https://fastapi.tiangolo.com --enhance

# Sync an existing config
/yonyou-doc2skill:sync-config react
```

Or just ask Claude naturally:
> "Create an AI skill from the React documentation"
> "Scrape the Flask GitHub repo and package it for OpenAI"
> "Export my skill to a Chroma vector database"

The skill-builder agent skill will automatically detect the intent and use the right tools.

## Remote MCP Alternative

By default, the plugin runs the MCP server locally via `python -m yonyou_doc2skill.mcp.server_fastmcp`. To use a remote server instead, edit `.mcp.json`:

```json
{
  "yonyou-doc2skill": {
    "type": "http",
    "url": "https://your-hosted-server.com/mcp"
  }
}
```

## Supported Source Types

Documentation (web), GitHub repos, PDFs, Word docs, EPUBs, videos, local codebases, Jupyter notebooks, HTML files, OpenAPI specs, AsciiDoc, PowerPoint, RSS/Atom feeds, man pages, Confluence, Notion, Slack/Discord exports.

## License

MIT — https://github.com/yonyou/yonyou-doc2skill
