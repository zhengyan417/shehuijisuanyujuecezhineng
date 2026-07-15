# AGENT_PROMPTS — paste into each teammate's coding agent

## Common prefix (every agent)

```text
You are collaborating in repo silent-demand Beijing course project.
Read AGENTS.md then collab/00_READ_THIS_FIRST.md before any edit.
Obey MODULE_OWNERS exclusive paths.
Keep city=北京 and only facility scopes road_lighting, public_charging, public_transit.
ABSOLUTELY NO fake/fixture social posts as project data. Without real crawl/import, fail.
After changes run: python -m pytest -q
Commit with ROLE and CONTRACT_IMPACT trailers per collab/GIT_WORKFLOW.md.
```

## Lab1 session prompt

```text
ROLE=AGENT_LAB1
Follow collab/guides/LAB1_AGENT.md.
Improve collection/cleaning only under owned paths.
Maintain fixture fallback so offline demo never breaks.
Get real Weibo data via cookie crawl; never invent/fake posts for demos.
Do not edit lab2/lab3 trees or configs/need_mapping.yaml.
If you need schema changes, write collab/inbox note and stop before breaking contract.
```

## Lab2 session prompt

```text
ROLE=AGENT_LAB2
Follow collab/guides/LAB2_AGENT.md.
Focus on intent+emotion+entities+need mapping domain adaptation.
Owned paths only. Keep enums valid.
Do not weaken complaint-to-need mapping into plain polarity classification.
```

## Lab3 session prompt

```text
ROLE=AGENT_LAB3
Follow collab/guides/LAB3_AGENT.md.
Build decision-support outputs from analyzed JSONL.
Keep recommendations advisory. Prefer grounding on aggregated counts/urgency.
Do not modify lab1/lab2 algorithms.
```

## Shared contract session prompt

```text
ROLE=SHARED
You may edit src/common, schemas, pipeline orchestration, and collab contracts.
Use additive changes first. Update models+schemas+producers+consumers+tests+DATA_CONTRACT together.
Notify other roles via collab/inbox/shared_to_all_*.md.
```
