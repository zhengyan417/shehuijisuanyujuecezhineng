# DATA_CONTRACT — inter-lab payloads

**Source of truth order:**

1. `src/common/models.py` (runtime enforcement)
2. `schemas/*.schema.json` (documentation + optional validation)
3. This file (behavioral contract + invariants)

If conflict: fix code/schema to match intentional design, then update this file in same SHARED change.

## Artifact flow

| Stage | Producer | Default path | Model |
| --- | --- | --- | --- |
| raw | LAB1 | `data/raw/*.jsonl` or fixture | `PostRaw` |
| cleaned | LAB1 | `data/cleaned/beijing_cleaned.jsonl` | `PostCleaned` |
| analyzed | LAB2 | `data/analyzed/beijing_analyzed.jsonl` | `PostAnalyzed` |
| report | LAB3 | `data/reports/beijing_silent_demand.{json,md}` | `DecisionReport` |

## Invariants

1. `city` MUST be `"北京"` for all project records in this course sprint.
2. JSONL = one JSON object per line, UTF-8, no trailing comma arrays file.
3. LAB1 writes cleaned records with `meta.dropped=false` into `beijing_cleaned.jsonl`.
4. LAB1 may also write audit file `beijing_cleaned_with_drops.jsonl` including dropped rows.
5. LAB2 MUST NOT invent new required upstream fields; if needed, open SHARED contract change.
6. LAB3 MUST tolerate `mapped_need.need_id = null` by skipping those rows in aggregation.
7. `geo.district` may be null; LAB3 buckets null as `未定位/全市`.
8. Enum fields must stay within model literals:
   - intent: `抱怨|建议|询问|其他`
   - emotion: `不满|焦虑|期待|中性`
   - facility_scope: `road_lighting|public_charging|public_transit`

## Breaking vs additive changes

### Additive (preferred)

- Add optional field with default
- Add new mapping rule id
- Add new need catalog id (also update LAB3 action template)

### Breaking (requires SHARED protocol)

- Rename/remove field
- Change enum values
- Change meaning of urgency_score scale
- Change default filenames consumed by next lab

## Filename stability

Downstream scripts hardcode defaults:

- Lab2 reads `data/cleaned/beijing_cleaned.jsonl`
- Lab3 reads `data/analyzed/beijing_analyzed.jsonl`

If renaming, update all of: producer, consumer scripts, tests, this contract — in one SHARED PR.

## Version fields

- `PostCleaned.meta.lab1_version`
- `PostAnalyzed.meta.lab2_version` (+ preserves lab1_version)
- `DecisionReport.meta.lab3_version`

Bump version string whenever behavior of that lab changes meaningfully.
