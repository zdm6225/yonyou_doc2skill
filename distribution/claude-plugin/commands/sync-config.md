---
description: Sync a scraping config's URLs against the live documentation site
---

# Sync Config

Synchronize a Yonyou Doc2Skill config file with the current state of a documentation site. Detects new pages, removed pages, and URL changes.

## Usage

```
/yonyou-doc2skill:sync-config <config-path-or-name>
```

## Instructions

When the user provides a config path or preset name via `$ARGUMENTS`:

1. If it's a preset name (e.g., `react`, `godot`), look for it in the `configs/` directory or fetch from the API.
2. Run the sync command:
   ```bash
   yonyou-doc2skill sync-config "$CONFIG"
   ```
3. Report what changed: new URLs found, removed URLs, and any conflicts.
4. Ask the user if they want to update the config and re-scrape.

## Examples

```
/yonyou-doc2skill:sync-config configs/react.json
/yonyou-doc2skill:sync-config react
```
