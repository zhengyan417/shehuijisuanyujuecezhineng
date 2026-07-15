# LAB2_AGENT guide

ROLE=`AGENT_LAB2`

## Objective

Convert **real** cleaned posts into analyzed posts.

## Hard rule

绝对禁止假数据。Lab2 只能消费 Lab1 从真实 crawl/import 产出的 `data/cleaned/beijing_cleaned.jsonl`。没有上游真数据就不要跑 Lab2 充数。

## Owned paths

- `src/lab2_analysis/**`
- `configs/need_mapping.yaml`
- `scripts/run_lab2.py`
- optional `tests/lab2/**` (unit tests may use tiny synthetic strings; never as project dataset)

## Required outputs

- `data/analyzed/beijing_analyzed.jsonl`
- `data/analyzed/lab2_analysis_report.json`
