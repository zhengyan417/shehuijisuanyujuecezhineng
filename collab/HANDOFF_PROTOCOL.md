# HANDOFF_PROTOCOL

Use this when transferring work across labs or when SHARED contracts change.

## Daily handoff packet (recommended)

Write to `collab/inbox/` at end of a lab work session:

```md
FROM: AGENT_LAB1
TO: AGENT_LAB2
BLOCKER: no
NEED_BY: 2026-07-16
STATUS: cleaned artifact ready
ARTIFACTS:
- data/cleaned/beijing_cleaned.jsonl (local only; recreate via scripts/run_lab1.py)
- fixture updated: yes/no
CONTRACT_IMPACT: none
NOTES:
- district fallback coverage...
ASK:
- please validate intent labels on lighting samples
```

Important: do **not** rely on committing large `data/` outputs. Handoff by making `scripts/run_labN.py` reproducible from fixtures/configs.

## Upstream readiness gates

### Lab1 -> Lab2 gate

Lab2 may start model work anytime against fixture+cleaned schema, but integration requires:

- `python scripts/run_lab1.py` succeeds
- output validates as `PostCleaned`
- at least one record per facility scope in samples

### Lab2 -> Lab3 gate

- `python scripts/run_lab2.py` succeeds
- `mapped_need` populated for majority of in-scope samples
- urgency in [0,1]

### Lab3 -> Presentation gate

- report md/json generated
- priorities non-empty on fixture pipeline
- method notes mention taxonomy + mapping + decision support framing

## Shared contract change procedure

1. Open inbox note `shared_to_all_*` describing additive/breaking impact
2. Implement in `shared/*` branch
3. Touch order:
   - `src/common/models.py`
   - `schemas/*.schema.json`
   - producers
   - consumers
   - tests
   - `collab/DATA_CONTRACT.md`
4. Run full pipeline
5. Merge
6. Notify all roles that their local branches should rebase on main

## Blocking etiquette

If blocked > 2 hours wall-clock during course day:

1. Write inbox blocker note
2. Continue on non-blocked subtask (tests, docs, fixtures, ablations)
3. Do not invent a private incompatible schema to unblock yourself
