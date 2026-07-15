# shared → all — additive field notice

```md
FROM: AGENT_LAB1
TO: AGENT_LAB2, AGENT_LAB3, SHARED
BLOCKER: no
NEED_BY: 2026-07-16
REQUEST:
- Acknowledge additive PostCleaned.meta.is_mediated: bool = false
- Lab2/Lab3: optional use; no required consumer change
CONTRACT_IMPACT: additive
PROPOSED_FILES:
- src/common/models.py (Lab1Meta.is_mediated)
- schemas/post_cleaned.schema.json
- collab/DATA_CONTRACT.md
```

Semantics: mediated = second-hand reporting of unresolved citizen facility demand (接诉/媒体转述).
Closed-case publicity posts are dropped by Lab1, not marked mediated.
