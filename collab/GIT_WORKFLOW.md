# GIT_WORKFLOW — multi coding-agent safe protocol

## Branches

- `main` = always runnable demo (`python scripts/run_pipeline.py` green)
- feature branches required for all non-trivial work

Branch prefixes:

- `lab1/...`
- `lab2/...`
- `lab3/...`
- `shared/...`

## Commit message format

```text
<source>: <imperative summary>

ROLE=<ROLE_ID>
CONTRACT_IMPACT=none|additive|breaking
```

Examples:

```text
lab2: add charging occupancy mapping rules

ROLE=AGENT_LAB2
CONTRACT_IMPACT=none
```

```text
shared: add optional geo.confidence_source field

ROLE=SHARED
CONTRACT_IMPACT=additive
```

## Sync rules for parallel agents

1. Start from updated `main`:
   ```bash
   git fetch origin
   git checkout main
   git pull --ff-only origin main
   git checkout -b labX/topic
   ```
2. Rebase or merge `main` into your branch before PR/push final.
3. Never rewrite history on `main`.
4. Avoid `git add .` when dirty shared files exist; stage owned paths explicitly.

## Suggested sparse staging examples

Lab1:

```bash
git add src/lab1_collection configs/keywords_taxonomy.yaml scripts/run_lab1.py fixtures/sample_raw
```

Lab2:

```bash
git add src/lab2_analysis configs/need_mapping.yaml scripts/run_lab2.py tests/lab2
```

Lab3:

```bash
git add src/lab3_decision scripts/run_lab3.py tests/lab3
```

## PR / merge checklist (agent must verify)

- [ ] ROLE declared
- [ ] no files outside ownership (or SHARED protocol followed)
- [ ] `python scripts/run_pipeline.py` OK
- [ ] `python -m pytest -q` OK
- [ ] DATA_CONTRACT updated if needed
- [ ] inbox note closed/answered if this PR unblocks someone

## Remote collaboration note

When remote URL is provided:

```bash
git remote add origin <URL>
git push -u origin main
```

Each teammate/agent clones same repo, claims role in `collab/ROLE_CLAIM.md`, then works on role branches.

## Conflict handling

If merge conflict in:

- owned file -> owner resolves
- shared file -> create `shared/resolve-<topic>` and follow CONFLICT_ZONES lock protocol
