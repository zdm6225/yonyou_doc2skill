# Yonyou Doc2Skill Design

## Goal

Fork `Yonyou Doc2Skill` into a branded external-facing product named `Yonyou Doc2Skill` with the primary CLI entrypoint:

```bash
yonyou-doc2skill create ...
```

The product should preserve the existing core workflow model while narrowing source coverage and removing non-target scenarios from the public product surface.

## Product Positioning

`Yonyou Doc2Skill` is an external-facing knowledge-to-skill packaging tool focused on turning selected documentation and code sources into AI-usable knowledge assets.

It is not a generic all-source ingestion platform in the first release. The public product surface should be narrower, clearer, and more coherent than the upstream fork.

## Chosen Strategy

Adopt a **complete white-label fork** with **public-surface narrowing**.

This means:
- Replace upstream branding in user-facing product surfaces.
- Rename package and primary CLI to `yonyou-doc2skill`.
- Keep the command model centered on `create`.
- Remove selected source scenarios from CLI entrypoints, docs, test expectations, and packaging metadata.
- Do **not** physically delete all underlying implementation files in the first phase unless required by packaging or dependency conflicts.

## Supported Sources In V1

Keep these public scenarios:
- Documentation websites
- GitHub repositories
- Local codebases / local directories
- PDF
- Word (`.docx`)
- Local HTML
- AsciiDoc
- PowerPoint (`.pptx`)
- Video (URL / local file)
- Confluence
- Slack / Discord chat export or chat ingestion

## Removed Sources In V1

Remove these from the public product surface:
- EPUB
- Jupyter Notebook
- OpenAPI / Swagger
- RSS / Atom
- Man page
- Notion

## Scope Of Branding Changes

Branding must be replaced in all public-facing product surfaces that affect external perception or installation:
- `pyproject.toml` package metadata
- primary console scripts
- README and key documentation entry pages
- plugin metadata (`.codex-plugin/plugin.json`)
- MCP/config examples that reference upstream brand
- help text and command descriptions where upstream brand is visible
- homepage / repository metadata should be replaced with Yonyou-controlled destinations if available; otherwise temporary internal placeholders are acceptable for phase 1 and must be clearly marked for later release cleanup

Branding replacement does **not** require exhaustive replacement inside internal architecture docs, historical changelogs, or generated UML assets in phase 1 unless they are exposed in the main distribution path.

## CLI Design

### Primary Command

The primary command remains:

```bash
yonyou-doc2skill create ...
```

### Command Philosophy

Preserve the existing command structure where possible to minimize regression risk.

### Public CLI Expectations

The public CLI should:
- expose `create` as the main user path
- expose retained dedicated commands that are still in-scope, especially `confluence` and `chat` if they remain productized
- stop advertising and stop accepting removed source scenarios through parser registration, source detection, help text, and docs

## Removal Strategy

Use a **surface-first removal** approach.

### Phase 1 Removal

Remove unwanted scenarios from:
- source detection pathways used by `create`
- parser registration and command help
- documentation and examples
- package metadata / optional dependency exposure where applicable
- automated tests that define the public contract

### Phase 1 Non-Removal

Do not prioritize deleting every internal implementation file for removed sources. Internal code may remain temporarily if:
- it is not publicly reachable
- it does not create packaging conflicts
- it does not create misleading docs/help/install paths

This reduces regression risk while delivering a clean external product surface.

## Packaging Strategy

### Package Identity

- Python package name: `yonyou-doc2skill`
- Main CLI: `yonyou-doc2skill`

### Script Policy

For the external-facing build, old `yonyou-doc2skill*` script names should not be the primary public interface.

Preferred direction:
- add `yonyou-doc2skill` command family
- optionally keep legacy aliases only during an internal transition period, but do not document them externally

Because this is an external product fork, the preferred end state is **new-name-first**, not dual-brand-first.

## Dependency Strategy

Trim optional dependencies that only support removed public scenarios where safe.

Initial target removals from public packaging surface:
- `epub`
- `jupyter`
- `notion`
- `rss`

OpenAPI / manpage may also require cleanup in docs/tests and detection pathways even if transitive dependencies are small.

Dependency cleanup should avoid breaking retained scenarios.

## Documentation Strategy

The documentation should be rewritten around the narrowed product:
- product intro explains only retained value proposition
- supported-source lists include only retained scenarios
- install examples use `yonyou-doc2skill`
- usage examples center on `create`, `confluence`, and retained workflows
- removed scenarios disappear from quick-start, source matrix, and CLI reference

## Testing Strategy

Testing must shift from upstream feature completeness to public product contract.

Required updates:
- parser tests
- source detection tests
- source validation tests
- packaging/entrypoint tests
- docs/help snapshot expectations where applicable

If removed-source code remains internally, tests should still reflect the public contract: those scenarios are not supported.

## Risks

### Risk 1: Incomplete rebrand

User-visible upstream naming may remain in less obvious places such as plugin metadata, examples, help epilog text, package URLs, or README fragments.

Mitigation:
- perform targeted grep-based audit for `yonyou-doc2skill` and `Yonyou Doc2Skill`
- classify findings by public-facing vs internal/historical

### Risk 2: Partial feature removal causing inconsistent CLI

A source type may disappear from docs but still parse, or disappear from parser lists but remain in detector logic.

Mitigation:
- treat removal as a contract change across docs, parser layer, detector layer, and tests together

### Risk 3: Packaging mismatch

Package metadata, script entry points, plugin metadata, and docs may drift.

Mitigation:
- validate installed CLI name and help output from the built environment

### Risk 4: Over-deletion in first pass

Physically deleting source implementations too early may create collateral damage.

Mitigation:
- defer hard deletion until after surface-first productization is stable

## Recommended Implementation Sequence

1. Rebrand package metadata and primary CLI entry point to `yonyou-doc2skill`
2. Rebrand core public docs and plugin metadata
3. Remove the six unwanted scenarios from source detection, parser/help exposure, and public docs
4. Update tests to match the narrowed product contract
5. Trim optional dependencies and packaging metadata for removed scenarios
6. Verify install, help output, and representative retained-source workflows

## Success Criteria

The first release is successful when:
- users install and run `yonyou-doc2skill`
- public docs consistently describe `Yonyou Doc2Skill`
- removed sources are not advertised or accepted through the intended public interface
- retained sources continue to work
- the product reads as a coherent external product, not an obvious upstream rename patch

## Explicit Decisions

- Product name: `Yonyou Doc2Skill`
- Main command: `yonyou-doc2skill create ...`
- Strategy: complete white-label fork
- Removal mode: public-surface removal first, not immediate full source deletion
- Removed scenarios: EPUB, Jupyter, OpenAPI/Swagger, RSS/Atom, Man page, Notion
