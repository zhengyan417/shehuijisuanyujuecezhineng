# lab2 → all — additive field notice

```md
FROM: AGENT_LAB2
TO: AGENT_LAB3, SHARED
BLOCKER: no
NEED_BY: 2026-07-17
REQUEST:
- Acknowledge additive PostAnalyzed.meta.is_mediated: bool = false (pass-through from Lab1)
- Lab3: optional use for down-weight / segmentation; not required
CONTRACT_IMPACT: additive
PROPOSED_FILES:
- src/common/models.py (Lab2Meta.is_mediated)
- schemas/post_analyzed.schema.json
- collab/DATA_CONTRACT.md
```
