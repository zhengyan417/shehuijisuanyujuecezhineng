# LAB2_AGENT guide

ROLE=`AGENT_LAB2`

## Objective

Convert cleaned posts into analyzed posts with:
intent, emotion, entities, mapped_need, urgency_score.

## Owned paths

- `src/lab2_analysis/**`
- `configs/need_mapping.yaml`
- `scripts/run_lab2.py`
- optional `tests/lab2/**`

## Required outputs

- `data/analyzed/beijing_analyzed.jsonl`
- `data/analyzed/lab2_analysis_report.json`

## Domain adaptation focus (presentation-critical)

Do NOT stop at positive/negative sentiment.
This domain needs:

- intent: 抱怨 / 建议 / 询问 / 其他
- emotion: 不满 / 焦虑 / 期待 / 中性
- complaint-to-need mapping dictionary

## Current implementation (lab2-0.2.0)

Modules:
- `intent.py` / `emotion.py` / `ner.py` / `mapper.py` / `urgency.py` / `analyzer.py`
- mapping dictionary `configs/need_mapping.yaml` v2

Fixture pipeline result target: mapped_ratio ~= 1.0 on in-scope cleaned posts.

## Forbidden

- rewriting Lab1 cleaner in place
- writing Lab3 report logic
- editing keyword taxonomy ownership file except via inbox request

## Validation snippet

```bash
python scripts/run_lab1.py --source fixture
python scripts/run_lab2.py
python -c "import json; rows=[json.loads(l) for l in open('data/analyzed/beijing_analyzed.jsonl',encoding='utf-8')]; print(sum(1 for r in rows if r['mapped_need']['need_id']))"
```
