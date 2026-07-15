# AGENTS.md — READ THIS FIRST (all coding agents)

You are a coding agent collaborating on a **3-person / 3-agent** course project.

## Project one-liner

**Beijing silent public-service demand discovery**: translate social posts about
`road lighting` + `public charging` + `public transit (bus stop / overpass)`
into actionable municipal decision-support outputs.

Pipeline:

```text
Lab1 raw/clean -> Lab2 analyze/map need -> Lab3 aggregate/report
```

## Mandatory bootstrap (do in order, every session)

1. Read `AGENTS.md` (this file)
2. Read `collab/00_READ_THIS_FIRST.md`
3. Read `collab/MODULE_OWNERS.md` and identify **your role**
4. Read `collab/DATA_CONTRACT.md`
5. Read `collab/CONFLICT_ZONES.md`
6. Read `collab/GIT_WORKFLOW.md`
7. Read only your module guide:
   - Lab1 -> `collab/guides/LAB1_AGENT.md`
   - Lab2 -> `collab/guides/LAB2_AGENT.md`
   - Lab3 -> `collab/guides/LAB3_AGENT.md`
8. If integrating / changing shared code -> also read `collab/HANDOFF_PROTOCOL.md`

## Hard scope freeze

City = **北京** only.  
Facility scopes = **exactly these three**:

- `road_lighting`
- `public_charging`
- `public_transit`

Do **not** expand to parks / toilets / markets / other cities unless humans explicitly vote and update `configs/city_beijing.yaml` + this file in the same change set.

## Hard data policy

**绝对禁止假数据 / fixture 社交媒体样本作为项目数据。**  
没有 `data/raw/crawl_*.jsonl` 或 `data/raw/import_*.jsonl` 就不跑 Lab1→Lab3。  
没有真实数据时必须失败退出，而不是静默用样例冒充。

## Role map

| Role ID | Owns | Must not touch |
| --- | --- | --- |
| `AGENT_LAB1` | collection/cleaning | `src/lab2_analysis/**`, `src/lab3_decision/**`, `configs/need_mapping.yaml` |
| `AGENT_LAB2` | intent/emotion/NER/need map | `src/lab1_collection/**`, `src/lab3_decision/**`, `configs/keywords_taxonomy.yaml` |
| `AGENT_LAB3` | aggregation/report/LLM support UX | `src/lab1_collection/**`, `src/lab2_analysis/**`, keyword taxonomy ownership |

Shared conflict zone (`src/common/**`, `schemas/**`, `src/pipeline.py`, root orchestration docs): edit only via coordination protocol.

## Default commands

```bash
python -m pip install -r requirements.txt
python scripts/run_pipeline.py
python -m pytest -q
```

Single-lab:

```bash
python scripts/run_lab1.py
python scripts/run_lab2.py
python scripts/run_lab3.py
```

## Success criteria for any agent change

- Pipeline still runs: `python scripts/run_pipeline.py`
- Tests pass: `python -m pytest -q`
- Output files still validate against `src/common/models.py` fields
- You did not edit another agent's exclusive paths
- Commit message prefixes role: `lab1:`, `lab2:`, `lab3:`, or `shared:`

## Privacy / ethics

- Never store raw phone numbers, exact home addresses, or deanonymized user profiles
- Prefer hashed author ids if any author field is kept
- No doxxing / harassment collection queries
