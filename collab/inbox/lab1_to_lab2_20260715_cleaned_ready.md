# lab1 → lab2 handoff

```md
FROM: AGENT_LAB1
TO: AGENT_LAB2
BLOCKER: no
NEED_BY: 2026-07-16
STATUS: cleaned artifact ready — Lab1 INTEGRATION READY
ARTIFACTS:
- data/cleaned/beijing_cleaned.jsonl (~292 kept, lab1-llm-filter-0.6.0)
- data/cleaned/lab1_cleaning_report.json (pass=llm_refine)
- data/raw/crawl_weibo_beijing.jsonl (~1500; recreate path via scripts/run_weibo_crawl.py)
CONTRACT_IMPACT: additive
NOTES:
- Backend = crawl4weibo (scrapy weibo-search abandoned)
- Semantic filter = NVIDIA LLM; no keyword blacklist drops
- ABCD: A一手 keep; B转述 keep + meta.is_mediated=true; C办结 DROP; D外地 DROP
- Geo priority: district_hint > poi > geo_raw > text landmarks
- Scope skew: public_transit kept≈11 only — do not overfit transit conclusions
- Optional field: meta.is_mediated (default false). Preserve or use; do not drop mediated rows
ASK:
- Consume beijing_cleaned.jsonl with PostCleaned schema
- Prefer clean_text for NLP
- Validate intent/emotion/need_map especially on lighting + charging; note transit n small
- If is_mediated useful for Lab3, pass through Lab2Meta / analyzed payload without breaking required fields
```

Human owner Lab1: 甘和君. See also `collab/guides/LAB1_AGENT.md` and `LAB2_AGENT.md`.
