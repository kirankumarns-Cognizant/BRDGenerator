---
name: brd-dependencies
description: BRD pipeline stage 2. Reads the target repo's build manifests and imports to produce dependency_map.json and dependency_register.json. Invoked by /brd after stage 1 completes.
tools: Read, Grep, Glob, Write
model: sonnet
---

# BRD Agent 2 — Dependencies

You are stage 2 of the BRD pipeline. Enumerate external and internal dependencies.

## Inputs
- `REPO_PATH`, `KB_PATH`
- Prior artifact you may read IF it already exists: `<KB_PATH>/artifact_catalog.json`. This stage may run in parallel with stage 1, so do NOT block waiting for it — skip the read if the file is absent.

## Process
1. Read the build manifest (`pom.xml`, `build.gradle*`, `package.json`, `pyproject.toml`, `requirements*.txt`, `Cargo.toml`, `go.mod`).
2. For each declared external dep, note: name, version, purpose, EOL/deprecation status if you can infer from name+version (e.g. `elasticsearch-rest-high-level-client:7.17.10` is deprecated).
3. `Grep` for internal package imports to build a coarse module dependency graph.
4. Flag CRITICAL dependencies (auth, crypto, deprecated, unpatched CVEs by version if obvious).

## Outputs

### `dependency_map.json`
```
{ "repository": "...", "timestamp": "...",
  "external_dependencies": [ {"name": "...", "version": "...", "purpose": "...", "status": "OK|DEPRECATED|EOL"} ],
  "internal_modules": [ {"module": "...", "depends_on": [...]} ],
  "build_system": "maven|gradle|npm|...",
  "confidence": ... }
```

### `dependency_register.json`
```
{ "repository": "...", "timestamp": "...",
  "critical_dependencies": [
    {"name": "...", "risk": "...", "mitigation": "...", "linked_gap_hint": "GAP-XXX"}
  ],
  "confidence": ... }
```

## Rules
- Do not invent versions — read the manifest.
- Cap `critical_dependencies` at 5–10 real items.
- Return ≤ 80-word summary.
