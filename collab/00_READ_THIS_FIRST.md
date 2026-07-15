# 00_READ_THIS_FIRST — coding-agent collaboration constitution

Audience: **coding agents only**. Optimize for unambiguous machine + agent execution.

## Goal

Prevent multi-agent collisions while building one runnable pipeline for the course presentation.

## Non-negotiable rules

1. **One role per agent session.** Before editing, declare role in the commit/PR body:
   `ROLE=AGENT_LAB1|AGENT_LAB2|AGENT_LAB3|SHARED`
2. **Exclusive directories are hard ownership.** Editing another role's exclusive path is a protocol violation even if "quick fix".
3. **Schema is law.** `src/common/models.py` + `schemas/*.schema.json` define the only legal inter-module payloads.
4. **Downstream must not break upstream.** Lab2/Lab3 must consume Lab1/Lab2 artifacts without requiring private side-channel files.
5. **Fixture must keep pipeline green.** Even if crawl fails, `fixtures/sample_raw/beijing_sample_posts.jsonl` keeps demo alive.
6. **No silent contract changes.** Any field add/rename/remove = SHARED change + all labs updated in one coordinated series.
7. **Do not commit runtime dumps under `data/`** except empty markers. Use fixtures for reproducible samples.
8. **Branch naming encodes role:**
   - `lab1/<short-desc>`
   - `lab2/<short-desc>`
   - `lab3/<short-desc>`
   - `shared/<short-desc>`

## File ownership cheat sheet

### Exclusive (no cross-edit)

- Lab1: `src/lab1_collection/**`, `configs/keywords_taxonomy.yaml`, `scripts/run_lab1.py`, `fixtures/sample_raw/**` (Lab1 may update fixtures; others propose via issue/PR comment only)
- Lab2: `src/lab2_analysis/**`, `configs/need_mapping.yaml`, `scripts/run_lab2.py`
- Lab3: `src/lab3_decision/**`, `scripts/run_lab3.py`, `docs/report_templates/**` (if present)

### Shared (coordination required)

- `src/common/**`
- `schemas/**`
- `src/pipeline.py`
- `scripts/run_pipeline.py`
- `tests/test_pipeline.py`
- `AGENTS.md`, `collab/**`, `requirements.txt`

### Read-only reference for all

- course task brief / proposal markdown at repo root
- `方案分析文档.md`

## Communication artifacts (agent-readable)

When a blocked dependency exists, write a short file:

`collab/inbox/<from>_to_<to>_<yyyymmdd>_<topic>.md`

Example: `collab/inbox/lab2_to_lab1_20260715_missing_district.md`

Required sections in every inbox note:

```md
FROM: AGENT_LABx
TO: AGENT_LABy
BLOCKER: yes|no
NEED_BY: ISO date
REQUEST:
- concrete ask
CONTRACT_IMPACT: none|additive|breaking
PROPOSED_FILES:
- paths
```

## Definition of integration-ready

A lab is integration-ready when:

1. Its script runs independently with current upstream artifacts
2. It writes only to its owned output directory
3. `python scripts/run_pipeline.py` succeeds after merging the branch
4. No TODOs that leave invalid JSONL / partial writes

## Conflict resolution order

If two agents touch related behavior:

1. Preserve DATA CONTRACT first
2. Prefer additive fields over renames
3. Prefer Lab ownership of domain logic over pipeline orchestration hacks
4. Keep stub/fallback path working

## Forbidden actions

- Rewriting another lab's algorithm "because it's easier"
- Introducing a second parallel schema (`dict` ad-hoc) bypassing pydantic models
- Expanding facility scope without config + AGENTS scope update
- Force-push to `main`
- Committing secrets / cookies / API tokens
