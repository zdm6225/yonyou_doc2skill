# Yonyou Doc2Skill — Smithery MCP Registry

Publishing guide for the Yonyou Doc2Skill MCP server on [Smithery](https://smithery.ai).

## Status

- **Namespace created:** `yonyou`
- **Server created:** `yonyou/yonyou-doc2skill`
- **Server page:** https://smithery.ai/servers/yonyou/yonyou-doc2skill
- **Release status:** Needs re-publish (initial release failed — Smithery couldn't scan GitHub URL as MCP endpoint)

## Publishing

Smithery requires a live, scannable MCP HTTP endpoint for URL-based publishing. Two options:

### Option A: Publish via Web UI (Recommended)

1. Go to https://smithery.ai/servers/yonyou/yonyou-doc2skill/releases
2. The server already exists — create a new release
3. For the "Local" tab: follow the prompts to publish as a stdio server
4. For the "URL" tab: provide a hosted HTTP endpoint URL

### Option B: Deploy HTTP endpoint first, then publish via CLI

1. Deploy the MCP server on Render/Railway/Fly.io:
   ```bash
   # Using existing Dockerfile.mcp
   docker build -f Dockerfile.mcp -t yonyou-doc2skill-mcp .
   # Deploy to your hosting provider
   ```
2. Publish the live URL:
   ```bash
   npx @smithery/cli@latest auth login
   npx @smithery/cli@latest mcp publish "https://your-deployed-url/mcp" \
     -n yonyou/yonyou-doc2skill
   ```

### CLI Authentication (already done)

```bash
# Install via npx (no global install needed)
npx @smithery/cli@latest auth login
npx @smithery/cli@latest namespace show   # Should show: yonyou
```

### After Publishing

Update the server page with metadata:

**Display name:** Yonyou Doc2Skill — AI Skill & RAG Toolkit

**Description:**
> Transform 17 source types into AI-ready skills and RAG knowledge. Ingest documentation sites, GitHub repos, PDFs, Jupyter notebooks, videos, Confluence, Notion, Slack/Discord exports, and more. Package for 16+ LLM platforms including Claude, GPT, Gemini, LangChain, LlamaIndex, and vector databases.

**Tags:** `ai`, `rag`, `documentation`, `skills`, `preprocessing`, `mcp`, `knowledge-base`, `vector-database`

## User Installation

Once published, users can add the server to their MCP client:

```bash
# Via Smithery CLI (adds to Claude Desktop, Cursor, etc.)
smithery mcp add yonyou/yonyou-doc2skill --client claude

# Or configure manually — users need yonyou-doc2skill installed:
pip install yonyou-doc2skill[mcp]
```

### Manual MCP Configuration

For clients that use JSON config (Claude Desktop, Claude Code, Cursor):

```json
{
  "mcpServers": {
    "yonyou-doc2skill": {
      "command": "python",
      "args": ["-m", "yonyou_doc2skill.mcp.server_fastmcp"]
    }
  }
}
```

## Available Tools (35)

| Category | Tools | Description |
|----------|-------|-------------|
| Config | 3 | Generate, list, validate scraping configs |
| Sync | 1 | Sync config URLs against live docs |
| Scraping | 11 | Scrape docs, GitHub, PDF, video, codebase, generic (10 types) |
| Packaging | 4 | Package, upload, enhance, install skills |
| Splitting | 2 | Split large configs, generate routers |
| Sources | 5 | Fetch, submit, manage config sources |
| Vector DB | 4 | Export to Weaviate, Chroma, FAISS, Qdrant |
| Workflows | 5 | List, get, create, update, delete workflows |

## Maintenance

- Update description/tags on major releases
- No code changes needed — users always get the latest via `pip install`

## Notes

- Smithery CLI v4.7.0 removed the `--transport stdio` flag from the docs
- The CLI `publish` command only supports URL-based (external) publishing
- For local/stdio servers, use the web UI at smithery.ai/servers/new
- The namespace and server entity are already created; only the release needs to succeed
