# Lab 1 数据采集——完整设计文档（与代码一致）

> **版本**：`lab1-llm-filter-0.6.0` / taxonomy `version: 5`  
> **权威源**：运行行为以代码为准；契约以 `src/common/models.py` 为准。  
> **OWNER**：`AGENT_LAB1`  
> **同步日期**：2026-07-15  
> 协作交接摘要见 `collab/guides/LAB1_AGENT.md`。

本文面向**人读**：讲清「为什么这样设计」以及「代码里具体怎么做」。执行命令速查可跳到文末附录。

---

## 1. 设计目标与思想

### 1.1 Lab1 要解决什么

课程命题是：**北京市公共资源「沉默需求」发现**。Lab1 只负责：

> 从真实社媒（微博）拉到与北京三类公共设施相关的原始帖，洗净后变成 Lab2 能稳定消费的 `PostCleaned` JSONL。

| 三类设施（硬冻结） | 代码枚举 |
| --- | --- |
| 道路照明 | `road_lighting` |
| 公共充电 | `public_charging` |
| 公交站 / 天桥等过街设施 | `public_transit` |

Lab1 **不做**意图/情绪/需求映射（Lab2），**不做**决策报告（Lab3）。

### 1.2 核心设计思想（按优先级）

1. **真数据纪律**  
   绝对禁止 fixture / 假帖冒充项目数据。没有 `data/raw/crawl_*.jsonl` 或 `import_*.jsonl` → `CollectionError`，流水线硬失败。

2. **先广召回，再语义精筛**  
   - 爬取阶段：用 taxonomy 多组**紧拼关键词**多捞帖（慢性领域持续采样，不是灾害突发单次爆破）。  
   - 清洗阶段：**机械层只做**规范化 / 过短 / 近重 / 软设施提示 / 区划；**不再用关键词黑名单**判广告、小说、办结通稿。  
   - 语义层：NVIDIA LLM 按 ABCD 规则 Keep/Drop，并标 `is_mediated`。

3. **地点优先，但允许宽召回**  
   - 主召回：`望京路灯不亮` 这类「片区/区名 + 设施 + 症状」紧拼（微博搜索对无空格串更友好）。  
   - 辅召回：`北京路灯不亮`、`路灯不亮`，提高召回；噪声交给 LLM 丢掉（例如外地同名「劲松」、办结通稿）。

4. **结构化定位优先于正文猜地点**  
   Geo：`district_hint` → `poi` → `geo_raw` → 正文；避免「正文没写北京、但定位其实是北京」被误杀，同时减轻纯文本把青岛劲松误判成北京劲松（最终仍靠 LLM 看外地城市词）。

5. **沉默需求 ≠ 办结宣传**  
   保留「现在仍有问题」的一手抱怨与转述诉求；丢掉「已修复、市民表示满意」类通稿。转述帖保留时标记 `meta.is_mediated=true`，供 Lab2/Lab3 分段或降权，**不丢**。

6. **隐私**  
   作者只存 `author_id_hash`（SHA256 前 16 位），不存明文 UID / 手机 / 精确住址。

### 1.3 当前交付水位（一次真实跑通）

| 指标 | 约值 |
| --- | --- |
| raw（crawl merge） | ~1500 |
| 一筛后 kept | ~650 |
| 精筛后 kept | **~292** |
| 其中 `is_mediated` | ~43 |
| 路灯 / 充电 / 公交 | ~207 / ~74 / ~11 |

公交偏少是召回/话语分布问题，不是契约缺字段；需要时另开 `public_transit` 专采。

---

## 2. 端到端数据流

```text
configs/keywords_taxonomy.yaml (v5)
        │
        ▼
queries.build_queries(max_per_scope)     多层紧拼查询
        │
        ▼
crawler.crawl_queries()                  crawl4weibo.search_posts
        │  Cookie: secrets/weibo_cookie.txt 或 WEIBO_COOKIE
        ▼
data/raw/crawl_weibo_beijing.jsonl       PostRaw[]
        │
        ▼
collector.run_lab1()
        ├─ cleaner.clean_posts()           机械：normalize / short / dup / geo / soft scope
        ├─ llm_filter.apply_llm_filter()   可选一筛（NVIDIA，快模型）
        └─ （推荐）run_lab1_llm_refine.py  二次精筛（略好快模型）
        ▼
data/cleaned/beijing_cleaned.jsonl       仅 kept → Lab2
data/cleaned/beijing_cleaned_with_drops.jsonl
data/cleaned/lab1_cleaning_report.json
```

### Source 模式（`sources.SourceMode`）

| mode | 行为 |
| --- | --- |
| `auto`（默认） | 只读已有 `crawl_*` / `import_*`；没有就报错；**不会**偷偷联网 |
| `raw` | 同上，显式读 raw |
| `crawl` | 已有 crawl 则复用；否则 `live=True` 当场爬 |

`python scripts/run_pipeline.py` 走 Lab1 `auto`，必须先有真爬结果。

### 模块职责一览

| 文件 | 职责 |
| --- | --- |
| `queries.py` | taxonomy → `SearchQuery` 列表 |
| `crawler.py` | Cookie、crawl4weibo、Post→PostRaw、落盘 |
| `sources.py` | 装载策略 + 禁假数据 |
| `cleaner.py` | 机械清洗（**无**语义黑名单） |
| `geo.py` | 区划推断优先级 |
| `llm_filter.py` | 系统提示词 + 批判 + cache + refine |
| `collector.py` | 编排入口 |

已弃用：Scrapy `third_party/weibo-search`、`weibo_adapter.py`。当前后端只有 **`crawl4weibo`**。

---

## 3. 查询设计：词表 + 组合规则 + 为什么

配置：`configs/keywords_taxonomy.yaml`（`version: 5`）。  
生成：`src/lab1_collection/queries.py` → `build_queries()`。

### 3.1 为什么要自建词表，而不是搜「北京公共服务」

微博综合搜索噪声极大。我们按课程三个设施拆开，用居民口语里**设施名 × 故障/不便症状 ×（可选）沉默需求句式 × 地点**组合，把搜索框变成「窄而多」的探针，更接近慢性民生抱怨，而不是新闻/段子/追星。

### 3.2 设施词表（完整）

#### road_lighting（道路照明）

| 维度 | 词 | 设计理由 |
| --- | --- | --- |
| labels | 路灯、道路照明、夜间照明、路灯杆、马路灯 | 「路灯」覆盖口语主峰；「道路/夜间照明」覆盖略正式表述；「杆/马路灯」补别称 |
| symptoms | 不亮、坏了、太黑、没路灯、漆黑、黑灯瞎火、半亮、忽明忽暗、摸黑 | 故障态 + 亮度体验；「摸黑/黑灯瞎火」常出现在真抱怨里 |
| need_cues | 没人管、晚上不敢走、什么时候能修好、希望修好、怎么不修、能不能修 | 沉默需求话术（催修、安全感），用于 `place_need` 层 |

#### public_charging（公共充电）

| 维度 | 词 | 设计理由 |
| --- | --- | --- |
| labels | 充电桩、充电站、公共充电、慢充、快充 | 桩/站口语都搜；慢充快充抓服务体验帖 |
| symptoms | 排队、被占位、不够用、找不到、充电难、充不上、离得远、坏了 | 占用与覆盖不足是充电侧主诉 |
| need_cues | 要是有就好了、能不能多装、希望多建、怎么不安、附近有充电吗 | 「愿望/缺失」句式，贴近沉默需求叙事 |

#### public_transit（公交站 / 天桥）

| 维度 | 词 | 设计理由 |
| --- | --- | --- |
| labels | 公交站、候车亭、天桥、过街天桥、站台 | 课程范围明确包含站与过街设施；不用「地铁」以免范围漂移 |
| symptoms | 不开、闲置、没遮雨、破损、太远、过马路危险、积水、台阶坏了 | 闲置天桥/破损亭/步行安全是真民生点 |
| need_cues | 什么时候能开放、希望修好、能不能修、没人管、过马路太危险 | 催开放、催维修 |

### 3.3 地点词（完整）

**hotspots（片区/商圈，优先带进查询）**  
望京、劲松、回龙观、天通苑、大峪、金盏、和平里、新风街、西二旗、五道口、中关村、通州北苑、亦庄、清河、国贸、三里屯、西单、上地、苹果园、良乡、后沙峪、石景山、双井、酒仙桥、北苑、亚运村  

**为何这些点**：提案/抽样里出现过的高暴露片区 + 充电/照明常见讨论区；「劲松」等有外地同名，**召回阶段照样搜**，**精筛阶段靠 LLM 看「青岛/成都…」DROP**（见 §6）。

**district_shorts（区名缩写，不带「区」）**  
朝阳、海淀、丰台、昌平、通州、大兴、门头沟、西城、东城、石景山、房山、顺义、怀柔、平谷、密云、延庆  

**为何**：覆盖全市 16 区尺度的「区+设施」帖，补 hotspot 列表以外的区域。

### 3.4 查询拼接规则（与代码一致）

`_compact(*parts)`：**去掉空白后直接拼接**，例如 `望京`+`路灯`+`不亮` → `望京路灯不亮`。

四个 layer：

| layer | 形态 | 例子 | 为什么要这层 |
| --- | --- | --- | --- |
| `place_symptom` | 地点+设施+症状 | `望京路灯不亮`、`朝阳充电桩排队` | **主召回**：空间可解释、噪声相对可控 |
| `place_need` | 地点+设施+cue（可再夹首症状） | `望京路灯没人管`、`望京路灯不亮没人管` | 专攻「催修/愿望」沉默表达 |
| `broad_bj` | `北京`+设施+症状/cue | `北京路灯不亮` | 中等宽度召回；依赖清洗/LLM 剔外地 |
| `facility_symptom` | 设施+症状/cue（无地点） | `路灯不亮`、`充电桩被占位` | **高召回**：压量时必开；噪声交给 LLM |

`collection_policy.allow_beijing_facility_symptom: true` 控制是否生成 `broad_bj`。  
政策注释：`avoid_bare_beijing_alone: true`——**不单独搜「北京」两个字**，避免整站热门流。

配额（默认 `max_per_scope=100`，脚本同默认）：

- place 层（symptom+need）≈ 55%（至少 40）
- broad_bj ≈ 25%（至少 15）
- facility_symptom ≈ 余量（至少 15）

当前 `build_queries(100)` ≈ **300 条**（每设施 100），layer 大致：`place_symptom` 最多，其次 `broad_bj`、`facility_symptom`。

#### 形态示例（真实生成）

```text
# road_lighting
望京路灯不亮          # place_symptom
望京路灯忽明忽暗
北京路灯太黑            # broad_bj
路灯没人管              # facility_symptom / need

# public_charging
望京充电桩排队
朝阳充电桩被占位
北京充电桩不够用
充电桩能不能多装

# public_transit
望京公交站没遮雨
望京天桥闲置
北京过街天桥不开
候车亭破损
```

Smoke 模式（`--smoke`）：每设施各取 **2 个不同 place** 的 place 层查询（约 6 条），只验证链路是否通。

### 3.5 备忘文件

`configs/weibo_keywords.txt` 仅人工备忘；**运行时不读**，以 `build_queries()` 为准。

---

## 4. 爬取实现（`crawler.py` + `run_weibo_crawl.py`）

### 4.1 为什么用 crawl4weibo

- pip 可装、Playwright Cookie/浏览器能力开箱，比维护 Scrapy `weibo-search` 子树轻。  
- 输出映射到项目 `PostRaw`，与 Lab2/Lab3 契约对齐。  
- 仓库内 Scrapy 路径已弃用，避免双后端漂移。

### 4.2 Cookie

优先级：`WEIBO_COOKIE` → `secrets/weibo_cookie.txt`（gitignore）。

处理：去注释行、拼接换行、剥 `Cookie:` 前缀；缺 `SUB=`/`SUBP=` 会警告。  
有 Cookie：`login_cookies=True` 注入；无 Cookie：`auto_fetch_cookies` + 无头浏览器访客 Cookie（搜索质量通常较差）。

### 4.3 调用与节流

```text
WeiboClient(rate_limit_config=RateLimitConfig(base_delay=(0.7d, 1.1d)), ...)
client.search_posts(query, page=page, use_proxy=False)
# 每页后再 sleep(delay_seconds)
```

脚本默认（可改）：`--pages 2`、`--delay 1.2`、`--max-posts 1500`、`--max-per-scope 100`。  
低压 delay 是为了多查询探查；过高会极慢，过低易触发风控（看 provenance `errors`）。

默认 **merge** 已有 `crawl_weibo_beijing.jsonl`（按 `id` 去重），方便多轮补采；`--no-merge` 可关。

### 4.4 Post → PostRaw

| 字段 | 来源 / 规则 |
| --- | --- |
| `id` | `wb_{id或bid}`；否则 md5(query+text)[:12] |
| `platform` | `"weibo"` |
| `text` | 去 HTML 后正文 |
| `time` | `created_at` ISO，缺省当前时间 |
| `city` | 固定 `"北京"`（项目范围约束；语义真伪再审） |
| `url` | `https://m.weibo.cn/detail/{bid}` |
| `author_id_hash` | SHA256(user_id)[:16] |
| `geo_raw` / `poi` | 微博 `location`（常空） |
| `facility_scope_hint` | 打出这条帖的查询所属 scope |
| `source_query` | 查询串（清洗可反推 place） |
| `district_hint` | 爬取阶段恒 `None` |

落盘：`data/raw/crawl_weibo_beijing.jsonl` + `crawl_weibo_beijing_provenance.json`（backend、每查询命中、errors…）。

---

## 5. 机械清洗与 Geo（`cleaner.py` / `geo.py`）

版本串：`LAB1_VERSION = "lab1-llm-filter-0.6.0"`。

### 5.1 机械层只做这些（重要）

| 步骤 | 行为 | `drop_reason` |
| --- | --- | --- |
| `normalize_text` | NFKC、去 URL/@、话题去 `#`、去 emoji、压空白 | — |
| 过短 | `len(clean_text) < 8` | `too_short` |
| 近重 | 去空白标点后 MD5；再见则丢 | `duplicate` |
| soft scope | hint 优先，否则 labels(+2)/symptoms(+1) 打分 | **从不因 out_of_scope 丢帖** |
| geo | 见下 | — |

**刻意不做**：广告词表、小说词表、外地黑名单、办结通稿规则——这些曾误杀（如截断 `...全文`）或与 LLM 重复；现全部交 §6。

### 5.2 Geo 优先级（代码注释与实现一致）

1. `district_hint`（置信 0.95）  
2. `poi` 字段内匹配地标/区名  
3. `geo_raw` 字段内匹配  
4. **fallback** 正文区名 / 地标表 `LANDMARK_TO_DISTRICT`  
5. 若仍无且 `source_query` 以 hotspot 开头（非仅「北京」），再用该 place 作 soft POI 推区  

**为什么**：微博大量帖正文不写「北京」，但定位或检索上下文是北京；反过来，正文写「劲松」也不能只靠字面当朝阳——外地消歧放在 LLM。

---

## 6. LLM 语义精筛（设计重点）

模块：`src/lab1_collection/llm_filter.py`  
脚本：`scripts/run_lab1_llm_filter.py`、`scripts/run_lab1_llm_refine.py`  
API：`NVIDIA_API_KEY` → `https://integrate.api.nvidia.com/v1`

### 6.1 两阶段为什么这样切

| 阶段 | 默认模型 | 环境变量 | 作用 |
| --- | --- | --- | --- |
| 一筛 | `nvidia/nemotron-mini-4b-instruct` | `LAB1_LLM_MODEL` | 快、便宜，从 raw 规模打到可用 kept |
| 精筛 | `meta/llama-3.1-8b-instruct` | `LAB1_LLM_REFINE_MODEL` | 稍强仍快；专收紧办结通稿 + 外地同名 |

对比试验过：部分 nano 模型超时/空响应；granite 404。故精筛固定 llama-3.1-8b。

批处理 + 线程池；cache：`llm_filter_cache.jsonl` / `llm_refine_cache.jsonl`。  
失败（`llm_error`）**不当作 DROP**，留给重跑，避免API抖动误杀上千条。

`run_lab1` 内一筛开关：环境变量 `LAB1_LLM_FILTER=1`（或脚本封装）。推荐流程：爬完 →（机械）→ 一筛 → 精筛。

### 6.2 ABCD 语义类别

| 类 | 含义 | 决策 |
| --- | --- | --- |
| **A** | 一手居民：未解决的抱怨/建议/询问 | Keep，`is_mediated=false` |
| **B** | 接诉/媒体转述「市民反映…」，且未办结 | Keep，`is_mediated=true` |
| **C** | 办结宣传（已修复、满意、点赞…） | **DROP** |
| **D** | 外地或同名街混淆（青岛劲松等） | **DROP** |

冲突裁决（提示词硬规则）：同一帖既有「市民反映」又有「已修复/已恢复」→ **优先 DROP（C）**，防止模型只看前半句 Keep。

代码侧额外保险：Keep 且正文含「市民反映 / 有市民 / 居民反映 / 网友反映 / 家长反映」→ 强制 `is_mediated=true`。

### 6.3 系统提示词（完整原文，与代码 `_SYSTEM` 一致）

```text
你是北京公共设施数据质检员。判断微博是否 KEEP。

【KEEP 必须同时满足】
1) 北京场景：发帖定位(geo_raw/poi)在北京，或正文明确北京区县/片区；不要把「劲松」等同名街道默认当成北京——若正文出现青岛/成都/湘潭/沈阳等外地城市，判 DROP。
2) 真实未解决需求：居民抱怨/建议/询问，或转述市民诉求，且问题仍在（不是已办结）。
3) 设施∈ 路灯照明(road_lighting) | 公共充电(public_charging) | 公交站/天桥(public_transit)。

【类别】
- A 一手居民抱怨：keep=true, is_mediated=false
- B 接诉/媒体转述「市民反映…」且无办结：keep=true, is_mediated=true
- C 办结宣传：keep=false（即使前半有市民反映）
- D 外地混淆：keep=false

【必须 DROP】
文学/小说/散文；粉丝应援；广告；仅风景心情；红绿灯/私家车等非三类设施；
办结通稿关键词（命中任一条优先 DROP）：已修复、已恢复正常、市民表示满意、值得点赞、及时响应、终于亮起来、解决居民烦心事、接诉后…已…。
特别注意：同一帖「市民反映」+「已修复/已恢复」→ 优先 DROP（办结通稿）。

只输出JSON数组，每项：
{"id":"...","keep":true/false,"is_mediated":true/false,"reason":"短中文","facility_scope":"road_lighting|public_charging|public_transit|null"}
```

### 6.4 User 消息模板（批判）

对每条帖构造（文本截断约 320 字）：

```text
请对下列微博逐条判断，返回等长JSON数组：
- id={id}
  geo_raw={geo_raw}
  poi={poi}
  district={district}
  text={text}
```

`temperature=0`；模型须返回 JSON 数组。解析失败单项会重试；仍失败则记 cache 错误并保持未丢弃以便 resume。

### 6.5 提示词设计意图（答辩可用）

- **把 geo 结构字段喂给模型**：弥补正文不写城市时的判断。  
- **外地城市点名**：专治「劲松」多城同名。  
- **办结关键词清单 + 冲突优先 DROP**：专治接诉通稿。  
- **设施白名单三 scope**：防止红绿灯、私家车、纯车评混入。  
- **强制 JSON schema 字段**：便于缓存与 `facility_scope_hint` 回写。

---

## 7. 契约与产物（下游认这个）

### 7.1 `PostCleaned`（正式 kept 文件）

```json
{
  "id": "wb_...",
  "platform": "weibo",
  "text": "原始正文",
  "clean_text": "规范化正文",
  "time": "...",
  "city": "北京",
  "geo": { "raw": null, "poi": "望京", "district": "朝阳区", "confidence": 0.65 },
  "meta": {
    "lab1_version": "lab1-llm-filter-0.6.0",
    "is_duplicate": false,
    "dropped": false,
    "drop_reason": null,
    "facility_scope_hint": "road_lighting",
    "is_mediated": false
  }
}
```

- `meta.is_mediated`：**additive**，默认 `false`；B 类为 `true`。Lab2 可透传/降权，勿当必填破坏项。  
- `geo.district` 可为 `null` → Lab3 桶为「未定位/全市」。  
- 早期示意稿里的 `location/user/is_valid` **不是**运行契约。

### 7.2 关键产物路径

| 路径 | 用途 |
| --- | --- |
| `data/raw/crawl_weibo_beijing.jsonl` | 真爬原始 |
| `data/cleaned/beijing_cleaned.jsonl` | **Lab2 唯一正式输入** |
| `data/cleaned/beijing_cleaned_with_drops.jsonl` | 审计（通常不入库） |
| `data/cleaned/lab1_cleaning_report.json` | kept/dropped/scopes；精筛后含 `pass=llm_refine` |

---

## 附录 A. 怎么跑（精简）

```bash
pip install -r requirements.txt
playwright install chromium
# Cookie → secrets/weibo_cookie.txt
# LLM → set NVIDIA_API_KEY

python scripts/run_weibo_crawl.py --smoke --run-lab1
python scripts/run_weibo_crawl.py --pages 3 --delay 1.2 --max-posts 1500
python scripts/run_lab1_llm_filter.py
python scripts/run_lab1_llm_refine.py
```

仅有 crawl、只重洗：`python scripts/run_lab1.py --source raw`。

## 附录 B. 边界

| Lab1 可改 | 勿擅改 |
| --- | --- |
| `src/lab1_collection/**`、`configs/keywords_taxonomy.yaml` | `src/lab2_analysis/**`、`configs/need_mapping.yaml`、`src/lab3_decision/**` |
| Lab1 scripts / `tests/lab1` | 擅自 breaking 改 `models.py`（须 SHARED） |

改查询策略、提示词或落盘约定时：**先改代码，再改本文，同一提交**。
