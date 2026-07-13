# CONTEXT — life-chart-engine

Ubiquitous language for this repo. Terms here are the canonical names; code, docs, and issues should use them consistently.

## Terms

### Chart System（盤面系統）
One of the three independent calculation systems: **Western natal**（西洋星盤, astronomy-engine）, **Human Design**（人類圖, derived from gate/center/channel tables）, **紫微斗數**（iztro Node sidecar）. They are computed independently and never merged — see Triangulation.

### Triangulation（交叉驗證）
The design principle that three independent Chart Systems corroborate each other. All three agree → high confidence; a single-system detail → reference point, not a verdict. This is the product's reason to exist alongside determinism; collapsing the three outputs into one would destroy it.

### Deterministic Chart Primitive
The engine's contract: same birth input → byte-identical output, offline, no state, no clock dependence. This is what makes the engine usable as an agent tool (an AI agent can *call* a chart instead of hallucinating one).

### Surface
An entry point that exposes the calculators: **CLI** (`scripts/chart_engine.py`), **HTTP server** (`server.py`), **local web UI** (`webapp.py`), **wrapper** (`bin/life-chart`). All surfaces must route through the same calculators / `build_json()`; duplicating calculation logic into a surface is a defect.

### Agent Contract
`AGENTS.md` + the `--json` envelope (`schema_version` 1.x family). Machine-facing; breaking shape changes bump the minor version and must update `AGENTS.md` and the README output reference together.

### Example-Person Fallback（範例人 fallback）
The historical CLI behaviour where omitted input flags silently fell back to a built-in example person. Treated as a defect of the CLI Surface (a wrong chart is worse than an error), not a feature.

### Hosted Version
The maintained web product built on this engine (linked from the README). The engine repo itself stays a pure, offline compute core; anything account-, payment-, or analytics-related belongs to the hosted version, never to this repo.
