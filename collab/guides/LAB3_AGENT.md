# LAB3_AGENT guide

ROLE=`AGENT_LAB3`

## Objective

Turn analyzed signals into decision-support products for municipal users.
Not autonomous decision replacement — advisory support only.

## Owned paths

- `src/lab3_decision/**`
- `scripts/run_lab3.py`
- optional `docs/report_templates/**`
- optional `tests/lab3/**`

## Required outputs

- `data/reports/beijing_silent_demand.json`
- `data/reports/beijing_silent_demand.md`

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

## Definition of done (Lab3)

1. Report generates from analyzed fixture pipeline
2. priorities ranked and non-empty
3. method notes mention: taxonomy rationale, mapping, decision support framing
4. full pipeline green

## Validation snippet

```bash
python scripts/run_pipeline.py
type data\reports\beijing_silent_demand.md
```
