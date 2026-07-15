# LAB1_AGENT guide

ROLE=`AGENT_LAB1`

## Objective

Produce Beijing cleaned posts from **REAL** Weibo crawl/import only.

## Hard rule

绝对禁止假数据。没有 `data/raw/crawl_*.jsonl` 或 `import_*.jsonl` 就不跑。

## Owned paths

- `src/lab1_collection/**`
- `configs/keywords_taxonomy.yaml`
- `configs/weibo_keywords.txt`
- `scripts/run_lab1.py`
- `scripts/run_weibo_crawl.py`
- `scripts/convert_weibo_to_lab1.py`
- `third_party/weibo-search/**`

## Real crawl

```bash
# secrets/weibo_cookie.txt required
python scripts/run_weibo_crawl.py --start 2026-06-01 --end 2026-07-15 --limit 80
python scripts/convert_weibo_to_lab1.py --run-lab1
```
