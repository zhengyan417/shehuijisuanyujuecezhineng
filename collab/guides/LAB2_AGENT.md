# LAB2_AGENT guide

ROLE=`AGENT_LAB2`

## Objective

Convert **real** cleaned posts into analyzed posts（intent / emotion / NER / need map）。

## Hard rule

绝对禁止假数据。Lab2 只能消费 Lab1 真实产物 `data/cleaned/beijing_cleaned.jsonl`。没有上游真数据就不要跑 Lab2 充数。

## Upstream from Lab1（2026-07-15 已就绪）

**Gate：Lab1 → Lab2 已通过。** 详见 `collab/inbox/lab1_to_lab2_20260715_cleaned_ready.md` 与 `collab/guides/LAB1_AGENT.md`。

| 项 | 值 |
| --- | --- |
| 输入文件 | `data/cleaned/beijing_cleaned.jsonl` |
| `lab1_version` | `lab1-llm-filter-0.6.0` |
| kept | ~292 |
| scopes | road_lighting≈207 / public_charging≈74 / **public_transit≈11（偏少）** |
| 模型 | `PostCleaned`（`src/common/models.py`） |

### 你必须知道的字段

- `clean_text`：主分析文本（优先于 `text`）
- `geo.district`：**可能为 null** → 下游按「未定位/全市」处理即可
- `meta.facility_scope_hint`：Lab1 软提示，**不是终审**；映射以你们的 `need_mapping.yaml` + 规则为准
- **`meta.is_mediated: bool`（新增 additive，默认 false）**  
  - `true` = B 类：接诉即办/媒体**转述**市民诉求，不是一手居民发帖  
  - Lab2 可选：单独统计、降权、或在 meta 原样传到 Lab3  
  - **不要因为 mediated 就丢掉**（Lab1 已认定仍是未解决需求）

### Lab1 已替你丢掉的噪声（无需再造一轮同类黑名单）

办结通稿、外地同名街（如青岛劲松）、文学/追星/纯广告等。仍建议对异常样本做抽检。

### 如何拿到数据

```bash
git pull
# 若仓库已含 beijing_cleaned.jsonl → 直接
python scripts/run_lab2.py

# 若本地没有 cleaned：向 Lab1 要文件，或在有 NVIDIA_API_KEY + crawl 时让 Lab1 重跑
# python scripts/run_lab1.py && python scripts/run_lab1_llm_refine.py
```

## Owned paths

- `src/lab2_analysis/**`
- `configs/need_mapping.yaml`
- `scripts/run_lab2.py`
- optional `tests/lab2/**`（单元测试可用极小合成字符串；不得当项目数据集）

## Required outputs

- `data/analyzed/beijing_analyzed.jsonl`
- `data/analyzed/lab2_analysis_report.json`

## Contract reminders

- 输出 `PostAnalyzed`；保留 `meta.lab1_version`，自填 `lab2_version`
- intent ∈ `抱怨|建议|询问|其他`
- emotion ∈ `不满|焦虑|期待|中性`
- facility_scope ∈ 三 scope
- `mapped_need.need_id` 可为 null（Lab3 会跳过）
- **禁止**改 Lab1 exclusive 路径；需要新上游字段 → SHARED + inbox

## Must not touch

`src/lab1_collection/**`、`src/lab3_decision/**`、`configs/keywords_taxonomy.yaml`
