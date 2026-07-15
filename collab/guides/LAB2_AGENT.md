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

## Domain adaptation focus (presentation-critical)

Do NOT stop at positive/negative sentiment.
This domain needs:

- intent: 抱怨 / 建议 / 询问 / 其他
- emotion: 不满 / 焦虑 / 期待 / 中性
- complaint-to-need mapping dictionary

## Allowed work

- replace stub rules with BERT/LLM classifiers
- improve NER lexicons or model-based NER
- expand need mapping rules for the 3 scopes only
- weak supervision / annotation utilities under lab2 tree

## Forbidden

- rewriting Lab1 cleaner in place
- writing Lab3 report logic
- editing keyword taxonomy ownership file except via inbox request

## Definition of done (Lab2)

1. Depends cleanly on Lab1 artifact path
2. Majority of in-scope samples get non-null `mapped_need.need_id`
3. Enum fields stay valid
4. urgency in [0,1]
5. `python scripts/run_lab2.py` + full pipeline green

## Validation snippet

```bash
python scripts/run_lab1.py
python scripts/run_lab2.py
python -c "import json; rows=[json.loads(l) for l in open('data/analyzed/beijing_analyzed.jsonl',encoding='utf-8')]; print(sum(1 for r in rows if r['mapped_need']['need_id']))"
```
