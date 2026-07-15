# CONFLICT_ZONES

## Red zones (high collision risk)

| Zone | Why dangerous | Rule |
| --- | --- | --- |
| `src/common/models.py` | breaks all labs | SHARED only; additive-first |
| `schemas/**` | doc/runtime drift | must match models in same PR |
| `src/pipeline.py` | orchestration | SHARED only |
| `configs/city_beijing.yaml` | scope freeze | SHARED + AGENTS scope update |
| Default artifact filenames | pipeline coupling | SHARED |

## Yellow zones (coordinate before write)

| Zone | Owner bias | Rule |
| --- | --- | --- |
| `fixtures/sample_raw/**` | LAB1 | LAB2/LAB3 request via inbox; LAB1 merges |
| `requirements.txt` | SHARED | declare why dependency needed |
| `tests/test_pipeline.py` | SHARED | keep end-to-end only |
| `collab/*.md` (except inbox) | SHARED | avoid contradictory edits |

## Green zones (safe parallel work)

| Zone | Owner |
| --- | --- |
| `src/lab1_collection/**` | LAB1 |
| `src/lab2_analysis/**` | LAB2 |
| `src/lab3_decision/**` | LAB3 |
| `configs/keywords_taxonomy.yaml` | LAB1 |
| `configs/need_mapping.yaml` | LAB2 |
| `tests/lab1/**` `tests/lab2/**` `tests/lab3/**` | respective |
| `collab/inbox/**` | any (additive) |

## Lock protocol for shared edits

Before editing a red zone:

1. Create branch `shared/<topic>`
2. Drop inbox notes to other two roles: `collab/inbox/shared_to_all_<date>_<topic>.md`
3. Implement additive change if possible
4. Update models + schemas + consumers
5. Run full pipeline + pytest
6. Merge only when no role objects in inbox reply within agreed window (or humans approve immediately for class)

## Emergency hotfix

If pipeline is red on `main`:

1. Prefer fix inside owning lab if root cause is local
2. If shared model bug: `shared/hotfix-<desc>` with minimal patch
3. Do not pile feature work into hotfix
