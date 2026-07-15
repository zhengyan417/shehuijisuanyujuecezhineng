# LAB1_AGENT guide

ROLE=`AGENT_LAB1`

## Objective

Produce reproducible Beijing cleaned posts for scopes:
`road_lighting`, `public_charging`, `public_transit`.

## Owned paths

- `src/lab1_collection/**`
- `configs/keywords_taxonomy.yaml`
- `configs/weibo_keywords.txt`
- `scripts/run_lab1.py`
- `scripts/run_weibo_crawl.py`
- `scripts/convert_weibo_to_lab1.py`
- `fixtures/sample_raw/**`
- `third_party/weibo-search/**` (vendored crawler)
- optional `tests/lab1/**`

## Required outputs

- `data/cleaned/beijing_cleaned.jsonl` (kept rows only)
- optional audit: `data/cleaned/beijing_cleaned_with_drops.jsonl`
- real crawl: `data/raw/crawl_weibo_beijing.jsonl`

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

## Real crawl (cookie required)

Vendored from https://github.com/dataabc/weibo-search -> `third_party/weibo-search`

```bash
pip install -r requirements.txt
# copy secrets/weibo_cookie.txt.example -> secrets/weibo_cookie.txt and paste Cookie
python scripts/run_weibo_crawl.py --start 2026-06-01 --end 2026-07-15 --limit 80
python scripts/convert_weibo_to_lab1.py --run-lab1
```

## Validation snippet

```bash
python scripts/run_lab1.py --source fixture
python -c "from pathlib import Path; print(sum(1 for _ in open('data/cleaned/beijing_cleaned.jsonl',encoding='utf-8')))"
```
