# LAB1_AGENT guide

ROLE=`AGENT_LAB1`

## Status (2026-07-15) — INTEGRATION READY

Lab1 **真爬 + 机械清洗 + LLM 语义筛 + 二次精筛** 已完成，可交接 Lab2。

| 指标 | 值 |
| --- | --- |
| `lab1_version` | `lab1-llm-filter-0.6.0` |
| raw（crawl merge） | ~1500 |
| 精筛后 kept | **292** |
| `is_mediated=true`（B 类转述） | 43 |
| road_lighting / public_charging / public_transit | 207 / 74 / 11 |

交付物（本机已生成；`beijing_cleaned.jsonl` + report 可入库方便队友直接接）：

- `data/raw/crawl_weibo_beijing.jsonl`
- `data/cleaned/beijing_cleaned.jsonl`（仅 kept）
- `data/cleaned/beijing_cleaned_with_drops.jsonl`（审计用，gitignore）
- `data/cleaned/lab1_cleaning_report.json`（`pass=llm_refine`）

设计细节见：`src/lab1_collection/Lab 1 数据采集——完整设计文档.md`（若版本号滞后，以本文件 + `cleaner.LAB1_VERSION` 为准）。

## Objective

Produce Beijing cleaned posts from **REAL** Weibo crawl only（`crawl4weibo`）。  
Scope 冻结：北京 + `road_lighting` / `public_charging` / `public_transit`。

## Hard rules

1. **绝对禁止假数据。** 无 `data/raw/crawl_*.jsonl` 或 `import_*.jsonl` 则 `CollectionError`，不得造行。
2. **语义筛靠 LLM，不用关键词黑名单**丢广告/小说/办结通稿。
3. Cookie / `NVIDIA_API_KEY` **永不入库**（`secrets/`、`.env`）。

## Owned paths

- `src/lab1_collection/**`
- `configs/keywords_taxonomy.yaml`
- `configs/weibo_keywords.txt`
- `scripts/run_lab1.py`
- `scripts/run_weibo_crawl.py`
- `scripts/run_lab1_llm_filter.py`
- `scripts/run_lab1_llm_refine.py`
- `scripts/convert_weibo_to_lab1.py`
- `tests/lab1/**`

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
# Cookie（推荐）: secrets/weibo_cookie.txt.example -> secrets/weibo_cookie.txt
# LLM: 环境变量 NVIDIA_API_KEY（NVIDIA NIM / integrate.api.nvidia.com）
```

## Pipeline（真实数据）

```text
crawl4weibo -> data/raw/crawl_weibo_beijing.jsonl
  -> mechanical clean (normalize / short / near-dup / soft facility hint / geo)
  -> LLM pass1 (nemotron-mini, fast)
  -> LLM refine (llama-3.1-8b, ABCD 收紧)
  -> data/cleaned/beijing_cleaned.jsonl
```

### 1) Crawl

```bash
# smoke
python scripts/run_weibo_crawl.py --smoke --run-lab1

# 正式（可 merge 旧 crawl）
python scripts/run_weibo_crawl.py --pages 3 --delay 1.2 --max-posts 1500 --run-lab1
```

### 2) 仅重跑清洗 / 一筛

```bash
python scripts/run_lab1.py
# 或显式
python scripts/run_lab1_llm_filter.py
```

### 3) 二次精筛（对当前 kept）

```bash
python scripts/run_lab1_llm_refine.py
```

默认模型：

- 一筛：`LAB1_LLM_MODEL` → `nvidia/nemotron-mini-4b-instruct`
- 精筛：`LAB1_LLM_REFINE_MODEL` → `meta/llama-3.1-8b-instruct`

缓存：`data/cleaned/llm_filter_cache.jsonl`、`llm_refine_cache.jsonl`（本地，gitignore）。

## 清洗语义（ABCD）

| 类 | 含义 | 处理 |
| --- | --- | --- |
| A | 一手居民未解决诉求 | Keep，`is_mediated=false` |
| B | 接诉/媒体转述「市民反映…」且未办结 | Keep，`is_mediated=true` |
| C | 办结通稿（已修复 / 市民表示满意 / 点赞…） | **DROP**；若「市民反映」+「已修复」并存 → 优先 DROP |
| D | 外地混淆（青岛/成都/湘潭等同名街） | **DROP** |

另 DROP：文学/追星/纯广告/无诉求风景心情。

## Geo 推断优先级（`geo.py`）

`district_hint` → `poi` → `geo_raw` → 正文地点词。  
避免「正文没写北京但定位是北京」被误杀。

## 契约（生产者）

输出必须符合 `PostCleaned`（`src/common/models.py`）。

- `city` 恒为 `"北京"`
- `meta.facility_scope_hint` ∈ 三 scope 或 null
- **`meta.is_mediated: bool`（additive，默认 false）** — Lab2/Lab3 可选用；B 类必为 true
- `meta.dropped=false` 才进入 `beijing_cleaned.jsonl`

## 已知局限（交接时说明）

1. **公交样本极少**（kept≈11）— 若 Lab2/Lab3 需要均衡样本，Lab1 需再开 `public_transit` 专采。
2. 精筛后仍可能有极少量营销文残留（靠抽检），非系统性外地劲松混入。
3. `third_party/weibo-search` 已弃用；当前后端是 **crawl4weibo**。
4. 无 `NVIDIA_API_KEY` 时不要指望本地再跑通语义筛；直接用已提交的 cleaned，或向 Lab1 要密钥/产物。

## Definition of done

- [x] 真实 crawl，无 fixture
- [x] `beijing_cleaned.jsonl` 校验 `PostCleaned`
- [x] 三 scope 均有 kept（公交偏少但非零）
- [x] LLM 语义筛 + 办结/外地规则
- [x] 交接文档已写（本文件 + inbox）

## Must not touch

`src/lab2_analysis/**`、`src/lab3_decision/**`、`configs/need_mapping.yaml`
