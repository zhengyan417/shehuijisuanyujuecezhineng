# ROLE_CLAIM

Fill once at project start. Coding agents: read this to know which role you are embodying in this clone.

| Role | Human name | Machine / agent label | Claimed at |
| --- | --- | --- | --- |
| AGENT_LAB1 | 甘和君 | coding-agent-lab1 | 2026-07-15 |
| AGENT_LAB2 | 牛浩凯 | coding-agent-lab2 | 2026-07-15 |
| AGENT_LAB3 | 李佳锦 | coding-agent-lab3 | 2026-07-15 |

## Module mapping

| Human | Role | Owns |
| --- | --- | --- |
| 甘和君 | AGENT_LAB1 | `src/lab1_collection/**`, `configs/keywords_taxonomy.yaml`, fixtures |
| 牛浩凯 | AGENT_LAB2 | `src/lab2_analysis/**`, `configs/need_mapping.yaml` |
| 李佳锦 | AGENT_LAB3 | `src/lab3_decision/**`, report generation |

Rules:
- Exactly one human per role.
- Do not switch roles mid-day without updating this file in a SHARED commit.
- Each coding-agent session must set working ROLE to the claimed Role ID above.
- Start prompts: see `collab/AGENT_PROMPTS.md`.
