# Workflows Guide

> **Yonyou Doc2Skill v3.2.0**  
> **Enhancement workflow presets for specialized analysis**

---

## What are Workflows?

Workflows are **multi-stage AI enhancement pipelines** that apply specialized analysis to your skills:

```
Basic Skill ──▶ Workflow: Security-Focus ──▶ Security-Enhanced Skill
                    Stage 1: Overview
                    Stage 2: Vulnerability Analysis
                    Stage 3: Best Practices
                    Stage 4: Compliance
```

---

## Built-in Presets

Yonyou Doc2Skill includes 6 built-in workflow presets:

| Preset | Stages | Best For |
|--------|--------|----------|
| `default` | 2 | General improvement |
| `minimal` | 1 | Light touch-up |
| `security-focus` | 4 | Security analysis |
| `architecture-comprehensive` | 7 | Deep architecture review |
| `api-documentation` | 3 | API documentation focus |
| `complex-merge` | 3 | Merging multiple source types into a unified skill |

---

## Using Workflows

### List Available Workflows

```bash
yonyou-doc2skill workflows list
```

**Output:**
```
Bundled Workflows:
  - default (built-in)
  - minimal (built-in)
  - security-focus (built-in)
  - architecture-comprehensive (built-in)
  - api-documentation (built-in)

User Workflows:
  - my-custom (user)
```

### Apply a Workflow

```bash
# During skill creation
yonyou-doc2skill create <source> --enhance-workflow security-focus

# Multiple workflows (chained)
yonyou-doc2skill create <source> \
  --enhance-workflow security-focus \
  --enhance-workflow api-documentation
```

### Show Workflow Content

```bash
yonyou-doc2skill workflows show security-focus
```

**Output:**
```yaml
name: security-focus
description: Security analysis workflow
stages:
  - name: security-overview
    prompt: Analyze security features and mechanisms...
    
  - name: vulnerability-analysis
    prompt: Identify common vulnerabilities...
    
  - name: best-practices
    prompt: Document security best practices...
    
  - name: compliance
    prompt: Map to security standards...
```

---

## Workflow Presets Explained

### Default Workflow

**Stages:** 2
**Purpose:** General improvement

```yaml
stages:
  - name: structure
    prompt: Improve overall structure and organization
  - name: content
    prompt: Enhance content quality and examples
```

**Use when:** You want standard enhancement without specific focus.

---

### Minimal Workflow

**Stages:** 1
**Purpose:** Light touch-up

```yaml
stages:
  - name: cleanup
    prompt: Basic formatting and cleanup
```

**Use when:** You need quick, minimal enhancement.

---

### Security-Focus Workflow

**Stages:** 4
**Purpose:** Security analysis and recommendations

```yaml
stages:
  - name: security-overview
    prompt: Identify and document security features...
    
  - name: vulnerability-analysis
    prompt: Analyze potential vulnerabilities...
    
  - name: security-best-practices
    prompt: Document security best practices...
    
  - name: compliance-mapping
    prompt: Map to OWASP, CWE, and other standards...
```

**Use for:**
- Security libraries
- Authentication systems
- API frameworks
- Any code handling sensitive data

**Example:**
```bash
yonyou-doc2skill create oauth2-server --enhance-workflow security-focus
```

---

### Architecture-Comprehensive Workflow

**Stages:** 7
**Purpose:** Deep architectural analysis

```yaml
stages:
  - name: system-overview
    prompt: Document high-level architecture...
    
  - name: component-analysis
    prompt: Analyze key components...
    
  - name: data-flow
    prompt: Document data flow patterns...
    
  - name: integration-points
    prompt: Identify external integrations...
    
  - name: scalability
    prompt: Document scalability considerations...
    
  - name: deployment
    prompt: Document deployment patterns...
    
  - name: maintenance
    prompt: Document operational concerns...
```

**Use for:**
- Large frameworks
- Distributed systems
- Microservices
- Enterprise platforms

**Example:**
```bash
yonyou-doc2skill create kubernetes/kubernetes \
  --enhance-workflow architecture-comprehensive
```

---

### API-Documentation Workflow

**Stages:** 3
**Purpose:** API-focused enhancement

```yaml
stages:
  - name: endpoint-catalog
    prompt: Catalog all API endpoints...
    
  - name: request-response
    prompt: Document request/response formats...
    
  - name: error-handling
    prompt: Document error codes and handling...
```

**Use for:**
- REST APIs
- GraphQL services
- SDKs
- Library documentation

**Example:**
```bash
yonyou-doc2skill create https://api.example.com/docs \
  --enhance-workflow api-documentation
```

---

### Complex-Merge Workflow

**Stages:** 3
**Purpose:** Merging multiple heterogeneous sources into a unified, coherent skill

```yaml
stages:
  - name: source-alignment
    prompt: Align and deduplicate content from different source types...
    
  - name: cross-reference
    prompt: Build cross-references between sources...
    
  - name: unified-synthesis
    prompt: Synthesize a unified narrative from all sources...
```

**Use for:**
- Multi-source unified configs (docs + GitHub + PDF + video)
- Combining documentation with chat history or wiki pages
- Any skill built from 3+ different source types

**Example:**
```bash
yonyou-doc2skill unified --config configs/multi-source.json \
  --enhance-workflow complex-merge
```

---

## Chaining Multiple Workflows

Apply multiple workflows sequentially:

```bash
yonyou-doc2skill create <source> \
  --enhance-workflow security-focus \
  --enhance-workflow api-documentation
```

**Execution order:**
1. Run `security-focus` workflow
2. Run `api-documentation` workflow on results
3. Final skill has both security and API focus

**Use case:** API with security considerations

---

## Custom Workflows

### Create Custom Workflow

Create a YAML file:

```yaml
# my-workflow.yaml
name: performance-focus
description: Performance optimization workflow

variables:
  target_latency: "100ms"
  target_throughput: "1000 req/s"

stages:
  - name: performance-overview
    type: builtin
    target: skill_md
    prompt: |
      Analyze performance characteristics of this framework.
      Focus on:
      - Benchmark results
      - Optimization opportunities
      - Scalability limits
    
  - name: optimization-guide
    type: custom
    uses_history: true
    prompt: |
      Based on the previous analysis, create an optimization guide.
      Target latency: {target_latency}
      Target throughput: {target_throughput}
      
      Previous results: {previous_results}
```

### Install Workflow

```bash
# Add to user workflows
yonyou-doc2skill workflows add my-workflow.yaml

# With custom name
yonyou-doc2skill workflows add my-workflow.yaml --name perf-guide
```

### Use Custom Workflow

```bash
yonyou-doc2skill create <source> --enhance-workflow performance-focus
```

### Update Workflow

```bash
# Edit the file, then:
yonyou-doc2skill workflows add my-workflow.yaml --name performance-focus
```

### Remove Workflow

```bash
yonyou-doc2skill workflows remove performance-focus
```

---

## Workflow Variables

Pass variables to workflows at runtime:

### In Workflow Definition

```yaml
variables:
  target_audience: "beginners"
  focus_area: "security"
```

### Override at Runtime

```bash
yonyou-doc2skill create <source> \
  --enhance-workflow my-workflow \
  --var target_audience=experts \
  --var focus_area=performance
```

### Use in Prompts

```yaml
stages:
  - name: customization
    prompt: |
      Tailor content for {target_audience}.
      Focus on {focus_area} aspects.
```

---

## Inline Stages

Add one-off enhancement stages without creating a workflow file:

```bash
yonyou-doc2skill create <source> \
  --enhance-stage "performance:Analyze performance characteristics"
```

**Format:** `name:prompt`

**Multiple stages:**
```bash
yonyou-doc2skill create <source> \
  --enhance-stage "perf:Analyze performance" \
  --enhance-stage "security:Check security" \
  --enhance-stage "examples:Add more examples"
```

---

## Workflow Dry Run

Preview what a workflow will do without executing:

```bash
yonyou-doc2skill create <source> \
  --enhance-workflow security-focus \
  --workflow-dry-run
```

**Output:**
```
Workflow: security-focus
Stages:
  1. security-overview
     - Will analyze security features
     - Target: skill_md
     
  2. vulnerability-analysis
     - Will identify vulnerabilities
     - Target: skill_md
     
  3. best-practices
     - Will document best practices
     - Target: skill_md
     
  4. compliance
     - Will map to standards
     - Target: skill_md

Execution order: Sequential
Estimated time: ~4 minutes
```

---

## Workflow Validation

Validate workflow syntax:

```bash
# Validate bundled workflow
yonyou-doc2skill workflows validate security-focus

# Validate file
yonyou-doc2skill workflows validate ./my-workflow.yaml
```

---

## Copying Workflows

Copy bundled workflows to customize:

```bash
# Copy single workflow
yonyou-doc2skill workflows copy security-focus

# Copy multiple
yonyou-doc2skill workflows copy security-focus api-documentation minimal

# Edit the copy
nano ~/.config/yonyou-doc2skill/workflows/security-focus.yaml
```

---

## Best Practices

### 1. Start with Default

```bash
# Default is good for most cases
yonyou-doc2skill create <source>
```

### 2. Add Specific Workflows as Needed

```bash
# Security-focused project
yonyou-doc2skill create auth-library --enhance-workflow security-focus

# API project
yonyou-doc2skill create api-framework --enhance-workflow api-documentation
```

### 3. Chain for Comprehensive Analysis

```bash
# Large framework: architecture + security
yonyou-doc2skill create kubernetes/kubernetes \
  --enhance-workflow architecture-comprehensive \
  --enhance-workflow security-focus
```

### 4. Create Custom for Specialized Needs

```bash
# Create custom workflow for your domain
yonyou-doc2skill workflows add ml-workflow.yaml
yonyou-doc2skill create ml-framework --enhance-workflow ml-focus
```

### 5. Use Variables for Flexibility

```bash
# Same workflow, different targets
yonyou-doc2skill create <source> \
  --enhance-workflow my-workflow \
  --var audience=beginners

yonyou-doc2skill create <source> \
  --enhance-workflow my-workflow \
  --var audience=experts
```

---

## Troubleshooting

### "Workflow not found"

```bash
# List available
yonyou-doc2skill workflows list

# Check spelling
yonyou-doc2skill create <source> --enhance-workflow security-focus
```

### "Invalid workflow YAML"

```bash
# Validate
yonyou-doc2skill workflows validate ./my-workflow.yaml

# Common issues:
# - Missing 'stages' key
# - Invalid YAML syntax
# - Undefined variable references
```

### "Workflow stage failed"

```bash
# Check stage details
yonyou-doc2skill workflows show my-workflow

# Try with dry run
yonyou-doc2skill create <source> \
  --enhance-workflow my-workflow \
  --workflow-dry-run
```

---

## Workflow Support Across All Scrapers

Workflows are supported by **all 17 source types** in Yonyou Doc2Skill:

| Scraper | Command | Workflow Support |
|---------|---------|------------------|
| Documentation | `scrape` | ✅ Full support |
| GitHub | `github` | ✅ Full support |
| Local Codebase | `analyze` | ✅ Full support |
| PDF | `pdf` | ✅ Full support |
| Word | `word` | ✅ Full support |
| EPUB | `epub` | ✅ Full support |
| Video | `video` | ✅ Full support |
| Jupyter Notebook | `jupyter` | ✅ Full support |
| Local HTML | `html` | ✅ Full support |
| OpenAPI/Swagger | `openapi` | ✅ Full support |
| AsciiDoc | `asciidoc` | ✅ Full support |
| PowerPoint | `pptx` | ✅ Full support |
| RSS/Atom | `rss` | ✅ Full support |
| Man Pages | `manpage` | ✅ Full support |
| Confluence | `confluence` | ✅ Full support |
| Notion | `notion` | ✅ Full support |
| Slack/Discord | `chat` | ✅ Full support |
| Unified/Multi-Source | `unified` | ✅ Full support |
| Create (Auto-detect) | `create` | ✅ Full support |

### Using Workflows with Different Sources

```bash
# Documentation website
yonyou-doc2skill scrape https://docs.example.com --enhance-workflow security-focus

# GitHub repository
yonyou-doc2skill github --repo owner/repo --enhance-workflow api-documentation

# Local codebase
yonyou-doc2skill analyze --directory ./my-project --enhance-workflow architecture-comprehensive

# PDF document
yonyou-doc2skill pdf --pdf manual.pdf --enhance-workflow minimal

# Unified config (multi-source)
yonyou-doc2skill unified --config configs/multi-source.json --enhance-workflow security-focus

# Auto-detect source type
yonyou-doc2skill create ./my-project --enhance-workflow security-focus
```

---

## Workflows in Config Files

Unified configs support defining workflows at the top level:

```json
{
  "name": "my-skill",
  "description": "Complete skill with security enhancement",
  "workflows": ["security-focus", "api-documentation"],
  "workflow_stages": [
    {
      "name": "cleanup",
      "prompt": "Remove boilerplate and standardize formatting"
    }
  ],
  "workflow_vars": {
    "focus_area": "performance",
    "detail_level": "comprehensive"
  },
  "sources": [
    {"type": "docs", "base_url": "https://docs.example.com/"}
  ]
}
```

**Priority:** CLI flags override config values

```bash
# Config has security-focus, CLI overrides with api-documentation
yonyou-doc2skill unified config.json --enhance-workflow api-documentation
```

---

## Summary

| Approach | When to Use |
|----------|-------------|
| **Default** | Most cases |
| **Security-Focus** | Security-sensitive projects |
| **Architecture** | Large frameworks, systems |
| **API-Docs** | API frameworks, libraries |
| **Complex-Merge** | Multi-source skills (3+ source types) |
| **Custom** | Specialized domains |
| **Chaining** | Multiple perspectives needed |

---

## Next Steps

- [Custom Workflows](../advanced/custom-workflows.md) - Advanced workflow creation
- [Enhancement Guide](03-enhancement.md) - Enhancement fundamentals
- [MCP Reference](../reference/MCP_REFERENCE.md) - Workflows via MCP
