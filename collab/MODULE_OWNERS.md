# MODULE_OWNERS

Assign human teammates to roles once, then keep stable for the 4-day project.

| Human slot | Role ID | Module | Primary objective |
| --- | --- | --- | --- |
| Member A | `AGENT_LAB1` | Data collection & cleaning | Produce valid `PostCleaned` JSONL for Beijing 3 scopes |
| Member B | `AGENT_LAB2` | Intent / emotion / NER / need mapping | Produce valid `PostAnalyzed` JSONL |
| Member C | `AGENT_LAB3` | Decision support generation | Produce report JSON + Markdown (+ optional chatbot later) |

## Ownership matrix (paths)

| Path | Owner | Others |
| --- | --- | --- |
| `src/lab1_collection/**` | LAB1 | read-only |
| `src/lab2_analysis/**` | LAB2 | read-only |
| `src/lab3_decision/**` | LAB3 | read-only |
| `configs/keywords_taxonomy.yaml` | LAB1 | read-only |
| `configs/need_mapping.yaml` | LAB2 | read-only |
| `configs/city_beijing.yaml` | SHARED | change rarely |
| `src/common/**` | SHARED | coordination |
| `schemas/**` | SHARED | coordination |
| `src/pipeline.py` | SHARED | coordination |
| `scripts/run_lab1.py` | LAB1 | read-only |
| `scripts/run_lab2.py` | LAB2 | read-only |
| `scripts/run_lab3.py` | LAB3 | read-only |
| `scripts/run_pipeline.py` | SHARED | coordination |
| `fixtures/sample_raw/**` | LAB1 | others request via inbox |
| `tests/test_pipeline.py` | SHARED | may add lab-local tests under `tests/labx/` |
| `collab/**` | SHARED | additive notes OK in `collab/inbox/` |

## Local lab tests (recommended)

Each owner may add:

- `tests/lab1/`
- `tests/lab2/`
- `tests/lab3/`

Do not put lab-specific brittle tests into `tests/test_pipeline.py` unless SHARED agreed.

## Role claim file

At project start, each human edits once:

`collab/ROLE_CLAIM.md`

Template already provided.
