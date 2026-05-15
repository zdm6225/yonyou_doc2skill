# IKM Connector Design

## Goal

Add a first-class `yonyou-doc2skill ikm` command for internal iKM knowledge assets. The first version supports knowledge-map extraction only: given a map `pk`, cookie, and portal/action location, it extracts map metadata, asset records, attachment metadata, optionally downloads attachments, and builds a reusable skill.

## Scope

- Add CLI command: `ikm`.
- Add mode: `--mode map`.
- Support auth via `--cookie` or `IKM_COOKIE`.
- Required map inputs: `--pk`, `--actionlocid`.
- Optional limits: `--max-assets`, `--download-attachments`.
- Generate `SKILL.md`, `references/index.md`, `references/assets.md`, `references/attachments.md`, and raw JSON files.

## Data Flow

1. `POST /knowledgemap/getKnowledgeMapByPK` fetches map metadata.
2. `POST /knowledgemap/getMapData` fetches map assets.
3. `GET /file/getHlDetail` fetches attachment metadata for each asset.
4. If enabled, `GET /file/downloadFileSingle` downloads attachments.
5. The converter writes normalized raw JSON and markdown references.

## Non-Goals

- Portal-wide crawl is not implemented in this version.
- Keyword search crawl is not implemented in this version.
- Attachment text extraction is not implemented in this version; downloaded files are saved for later parsing.
- No browser automation is used.

## Error Handling

- Missing cookie, map pk, or action location fails fast.
- Non-200 API `code` values raise an extraction error.
- Attachment metadata failures are recorded per asset and do not stop the whole run.
- Download failures are recorded in attachment metadata and do not stop skill generation.

## Tests

- CLI parser exposes the `ikm` command and arguments.
- Auth can be read from `IKM_COOKIE`.
- Map extraction calls the expected iKM endpoints and normalizes map, assets, and attachments.
- Skill output contains the expected file structure and key reference content.

