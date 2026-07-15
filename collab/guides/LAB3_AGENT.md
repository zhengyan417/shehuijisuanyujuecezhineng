# LAB3_AGENT guide

ROLE=`AGENT_LAB3`

## Objective

Turn analyzed signals into decision-support products for municipal users.
Not autonomous decision replacement — advisory support only.

## Upstream readiness

- Lab1 cleaned：**已就绪**（`lab1-llm-filter-0.6.0`，kept≈292）。见 `collab/guides/LAB1_AGENT.md`。
- Lab2 analyzed：等 Lab2 产出 `data/analyzed/beijing_analyzed.jsonl` 后做集成。

注意上游样本偏斜：**公交 kept 很少**；报告里对 `public_transit` 勿过度外推，可在 method notes 写明样本量。

## Owned paths

- `src/lab3_decision/**`
- `scripts/run_lab3.py`
- optional `docs/report_templates/**`
- optional `tests/lab3/**`

## Required outputs

- `data/reports/beijing_silent_demand.json`
- `data/reports/beijing_silent_demand.md`

## Optional field from Lab1（经 Lab2 透传时可注意）

`meta.is_mediated`（在 cleaned 上）：转述诉求 vs 一手发帖。若 Lab2 保留到 analyzed：

- 可在报告中分开展示「一手 vs 转述」
- 或对 mediated 样本降权；**不要静默丢弃**

`geo.district` 可为 null → bucket `未定位/全市`。

## Product options (pick at least one beyond markdown)

Stub currently provides JSON+MD. Extensions allowed:

- LLM brief generation grounded on aggregated stats
- simple Q&A CLI over gaps/priorities
- optional static HTML dashboard
- retrieve authority snippets (standards/guidelines) for grounding

## Allowed work

- aggregation scoring redesign
- prompt/skill design for generation
- visualization exports
- authority-knowledge stubs under lab3 tree

## Forbidden

- changing Lab2 label semantics silently
- requiring extra undocumented fields from Lab2 without SHARED change
- expanding to new facility scopes
- touching `src/lab1_collection/**` / `src/lab2_analysis/**`

## Definition of done (Lab3)

1. Report generates from analyzed pipeline
2. priorities ranked and non-empty
3. method notes mention: taxonomy rationale, mapping, decision support framing
4. full pipeline green

## Validation snippet

```bash
python scripts/run_pipeline.py
# Windows:
type data\reports\beijing_silent_demand.md
```
