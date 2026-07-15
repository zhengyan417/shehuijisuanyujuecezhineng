# LAB1_AGENT guide

ROLE=`AGENT_LAB1`

## Objective

Produce reproducible Beijing cleaned posts for scopes:
`road_lighting`, `public_charging`, `public_transit`.

## Owned paths

- `src/lab1_collection/**`
- `configs/keywords_taxonomy.yaml`
- `scripts/run_lab1.py`
- `fixtures/sample_raw/**`
- optional `tests/lab1/**`

## Required outputs

- `data/cleaned/beijing_cleaned.jsonl` (kept rows only)
- optional audit: `data/cleaned/beijing_cleaned_with_drops.jsonl`

## Allowed work

- crawler implementations / API clients
- cleaning, dedupe, geo inference improvements
- keyword taxonomy refinement inside frozen 3 scopes
- enlarge fixtures with realistic Beijing samples

## Forbidden

- editing Lab2/Lab3 source trees
- editing `configs/need_mapping.yaml`
- changing pydantic required fields without SHARED protocol

## Definition of done (Lab1)

1. `python scripts/run_lab1.py` succeeds without network if using fixture fallback
2. At least 1 kept sample per facility scope in fixture set
3. Duplicate near-identical texts dropped
4. Docs in taxonomy explain chronic/local sampling rationale
5. No PII raw values committed

## Suggested implementation order

1. Keep fixture pipeline green
2. Improve geo/district inference
3. Add real collector behind a flag, default offline
4. Record crawl failures and auto-fallback to fixture

## Validation snippet

```bash
python scripts/run_lab1.py
python -c "from pathlib import Path; print(sum(1 for _ in open('data/cleaned/beijing_cleaned.jsonl',encoding='utf-8')))"
```
