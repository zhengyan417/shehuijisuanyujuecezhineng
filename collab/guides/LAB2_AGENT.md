# LAB2_AGENT guide

ROLE=`AGENT_LAB2`

## Objective

Convert **real** cleaned posts into analyzed posts（intent / emotion / NER / need map）。

## Hard rule

绝对禁止假数据。Lab2 只能消费 Lab1 真实产物 `data/cleaned/beijing_cleaned.jsonl`。

## Status (lab2-0.3.0 — COMPLETE)

| 项 | 值 |
| --- | --- |
| 输入 | `data/cleaned/beijing_cleaned.jsonl` (1473, lab1-llm-filter-0.6.0) |
| 输出 | `data/analyzed/beijing_analyzed.jsonl` |
| 报告 | `data/analyzed/lab2_analysis_report.json` |
| mapped_ratio | ~0.65（无设施证据的噪声不映射） |
| pass-through | `meta.is_mediated` |

### Design choices

- Prefer `clean_text`
- Explicit mapping rules first; `SCOPE_FALLBACK` only with facility evidence
- Residual Lab1 noise (生日/广告/外地通稿残留) → `mapped_need.need_id=null`（Lab3 跳过）
- `public_transit` upstream n很小，勿过度解读

## Run

```bash
git pull
python scripts/run_lab2.py
python -m pytest -q tests/lab2
```

## Owned paths

- `src/lab2_analysis/**`
- `configs/need_mapping.yaml`
- `scripts/run_lab2.py`
- `tests/lab2/**`

## Must not touch

`src/lab1_collection/**`、`src/lab3_decision/**`、`configs/keywords_taxonomy.yaml`
