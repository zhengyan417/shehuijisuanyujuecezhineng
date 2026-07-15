# Lab 1 数据采集——实现说明（与代码一致）

> 本文档**忠实于当前仓库实现**（`lab1-crawl4weibo-0.4.0` / taxonomy `version: 4`）。  
> 契约权威源：`src/common/models.py`。若本文与代码冲突，以代码为准并回写本文。  
> OWNER：`AGENT_LAB1`（独占改 `src/lab1_collection/**`、`configs/keywords_taxonomy.yaml`、相关 scripts）。

---

## 1. Lab1 目标（代码实际做什么）

把**真实微博**帖子变成下游 Lab2 可消费的 `PostCleaned` JSONL。

| 硬约束（代码强制） | 说明 |
| --- | --- |
| 城市 | `city` 固定 `"北京"` |
| 设施范围 | 仅 `road_lighting` / `public_charging` / `public_transit` |
| 真数据 | **禁止** fixture / 假社媒样本；没有 `data/raw/crawl_*.jsonl` 或 `import_*.jsonl` 就 `CollectionError` |
| 爬虫后端 | `crawl4weibo`（`pip` 库），**不是**已废弃的 Scrapy `third_party/weibo-search` |
| 隐私 | 作者只存 `author_id_hash`（SHA256 前 16 位），不存明文 UID |

Lab1 **不**做意图/情绪/需求映射（那是 Lab2）；**不**写决策报告（Lab3）。

---

## 2. 端到端数据流

```text
configs/keywords_taxonomy.yaml
        │
        ▼
queries.build_queries()     ──► 无空格、地点优先检索串
        │                       例：望京路灯不亮 / 回龙观充电桩排队
        ▼
crawler.crawl_queries()     ──► crawl4weibo.search_posts(...)
        │                       Cookie: secrets/weibo_cookie.txt 或 WEIBO_COOKIE
        ▼
data/raw/crawl_weibo_beijing.jsonl          # PostRaw[]
data/raw/crawl_weibo_beijing_provenance.json
        │
        ▼
sources.collect_raw_posts(mode)             # auto|raw|crawl
        │
        ▼
collector.run_lab1()
        ├─ persist_raw_snapshot → data/raw/beijing_raw.jsonl (+ provenance + query_plan)
        ├─ cleaner.clean_posts → PostCleaned[]（含 dropped）
        └─ 写出：
              data/cleaned/beijing_cleaned.jsonl              # 仅 kept
              data/cleaned/beijing_cleaned_with_drops.jsonl   # kept+dropped
              data/cleaned/lab1_cleaning_report.json
        │
        ▼
Lab2 读取 beijing_cleaned.jsonl
```

### 2.1 `--source` 三种模式（`sources.SourceMode`）

| mode | 行为 |
| --- | --- |
| `auto`（默认） | **只读**已有 `data/raw/crawl_*.jsonl` / `import_*.jsonl`；没有就报错。**不会**偷偷联网爬。 |
| `raw` | 同上，显式读 raw 目录。 |
| `crawl` | `try_crawl_posts(live=True)`：已有 `crawl_*.jsonl` 则复用；否则当场调 `crawl_queries()` 再落盘。 |

全链路 `python scripts/run_pipeline.py` 走的是 Lab1 `auto`：必须先有真爬结果。

---

## 3. 目录与文件职责

### 3.1 包内模块（`src/lab1_collection/`）

| 文件 | 职责 |
| --- | --- |
| `__init__.py` | 导出 `run_lab1`、`keyword_coverage_report` |
| `collector.py` | **编排入口**：读源 → 快照 → `clean_posts` → 写 cleaned + 清洗报告 |
| `crawler.py` | **真爬**：Cookie 加载、`WeiboClient`、Post→`PostRaw`、落盘 `crawl_weibo_beijing.jsonl` |
| `queries.py` | 从 taxonomy 生成 `SearchQuery`（无空格拼接） |
| `cleaner.py` | 规范化、去噪、去重、范围过滤、区划推断 → `PostCleaned` |
| `geo.py` | 地标/区名 → `district` + confidence |
| `sources.py` | 原始数据装载策略 + `CollectionError`（禁假数据） |
| `README.md` | 一行入口提示 |
| `Lab 1 数据采集——完整设计文档.md` | 本文 |

已删除/弃用：`weibo_adapter.py`（原 Scrapy CSV 转换）。`third_party/weibo-search/` 仅历史参考，Lab1 运行路径不调用。

### 3.2 配置

| 路径 | OWNER | 含义 |
| --- | --- | --- |
| `configs/keywords_taxonomy.yaml` | Lab1 | 设施词 / 症状 / 暗示句式 / 地点列表；`version: 4` |
| `configs/city_beijing.yaml` | SHARED | 16 区名单（`geo.district_list` 用） |
| `configs/weibo_keywords.txt` | Lab1 | **人工备忘**示例查询；**运行时查询以 `build_queries()` 为准**，脚本不读此文件 |
| `secrets/weibo_cookie.txt` | 本地私密 | 登录 Cookie（`.gitignore`）；缺则浏览器访客 Cookie，搜索质量通常更差 |
| `secrets/weibo_cookie.txt.example` | 仓库 | Cookie 获取说明模板 |

### 3.3 脚本

| 脚本 | 作用 |
| --- | --- |
| `scripts/run_weibo_crawl.py` | 调 `crawl_queries` → `persist_crawl`；可选 `--run-lab1` |
| `scripts/run_lab1.py` | 只做清洗编排（默认 `--source auto`） |
| `scripts/convert_weibo_to_lab1.py` | 兼容旧名字：实质是 `run_lab1(source="raw")` |
| `scripts/run_pipeline.py` | Lab1→2→3；Lab1 无真数据会直接失败 |

### 3.4 运行时产物（默认不提交大文件）

| 路径 | 内容 |
| --- | --- |
| `data/raw/crawl_weibo_beijing.jsonl` | 爬虫写出的 `PostRaw` |
| `data/raw/crawl_weibo_beijing_provenance.json` | 爬取元信息（backend、queries、errors…） |
| `data/raw/beijing_raw.jsonl` | `run_lab1` 装载后的快照 |
| `data/raw/beijing_raw_provenance.json` | 装载 provenance |
| `data/raw/lab1_query_plan.json` | 当次 query 计划 |
| `data/cleaned/beijing_cleaned.jsonl` | **下游唯一正式输入**（仅 `meta.dropped=false`） |
| `data/cleaned/beijing_cleaned_with_drops.jsonl` | 含丢弃行（审计） |
| `data/cleaned/lab1_cleaning_report.json` | kept/dropped/scopes/district_coverage… |

### 3.5 测试

`tests/lab1/test_lab1.py`：查询形态、近重指纹、区划、噪声丢弃类别、无真数据时报错。单元测可用合成 `PostRaw`，**不得**作为项目数据集。

---

## 4. 查询设计（`queries.py` + taxonomy v4）

### 4.1 原则（已落地）

1. **地点优先**：每个查询带 hotspot 或区名缩写（望京 / 回龙观 / 朝阳…）。  
2. **无空格紧拼**：`_compact(place, label, symptom)` → `望京路灯不亮`。  
3. **禁止裸「北京」**：减轻模糊匹配带来的小说、外地、泛内容噪声。  
4. **暗示句式层**：`need_cues` 拼进查询，如 `望京路灯坏了没人管`。

### 4.2 Taxonomy 结构（`configs/keywords_taxonomy.yaml`）

```yaml
facility_types:
  road_lighting | public_charging | public_transit:
    labels:   [...]   # 设施词
    symptoms: [...]   # 问题表现
    need_cues:[...]   # 沉默需求暗示
place_hints:
  hotspots: [...]         # 望京、劲松、回龙观…
  district_shorts: [...]  # 朝阳、海淀…（不带「区」）
```

当前 facility 词表摘要：

| scope | labels 例 | symptoms 例 | need_cues 例 |
| --- | --- | --- | --- |
| road_lighting | 路灯、道路照明、夜间照明 | 不亮、坏了、太黑… | 没人管、晚上不敢走… |
| public_charging | 充电桩、充电站、公共充电 | 排队、被占位、不够用… | 要是有就好了、能不能多装… |
| public_transit | 公交站、候车亭、天桥、过街天桥 | 不开、闲置、没遮雨… | 什么时候能开放、希望修好… |

### 4.3 `build_queries(max_per_scope=32)` 组合规则

对每个 `(scope, place)`：

- `place + label[:2] + symptom[:4]` → layer=`place_symptom`
- `place + label[:2] + cue[:3]` → layer=`place_need`
- `place + label + first_symptom + cue` → layer=`place_need`
- `place + seed_label + first_symptom` → layer=`place_symptom`

然后按 query 字符串去重，并按 scope 截断到 `max_per_scope`。

`SearchQuery` 字段：`facility_scope`, `query`, `layer`, `place`。

Smoke 模式（`crawl_queries(smoke=True)`）：每个设施选 **2 个不同 place** 的 `place_symptom`/`place_need` 查询，约 6 条，用于试跑。

---

## 5. 爬取实现（`crawler.py`）

### 5.1 Cookie

优先级：环境变量 `WEIBO_COOKIE` → `secrets/weibo_cookie.txt`。

处理：去掉注释行、拼接换行、剥 `Cookie:` 前缀；若无 `SUB=`/`SUBP=` 会警告。

有 Cookie：`login_cookies=True`，注入 `cookies=`。  
无 Cookie：`auto_fetch_cookies=True`（Playwright 访客 Cookie）。

### 5.2 调用

```text
WeiboClient(rate_limit_config=..., browser_headless=True, ...)
client.search_posts(query, page=page, use_proxy=False)
```

额外 `time.sleep(delay_seconds)`（默认脚本 3.5s）。`RateLimitConfig.base_delay` 取 delay 的 0.8～1.2 倍。

### 5.3 `Post` → `PostRaw` 映射

| PostRaw 字段 | 来源 |
| --- | --- |
| `id` | `wb_{id或bid}`；否则 md5(query+text) 前 12 位 |
| `platform` | `"weibo"` |
| `text` | 去 HTML 标签后的正文 |
| `time` | `created_at` ISO；缺省则当前时间 |
| `city` | `"北京"` |
| `url` | `https://m.weibo.cn/detail/{bid}` |
| `author_id_hash` | SHA256(user_id)[:16] |
| `geo_raw` / `poi` | 微博 `location`（可空） |
| `facility_scope_hint` | 该条查询的 `SearchQuery.facility_scope` |
| `source_query` | 查询串（清洗阶段可反推 place） |
| `district_hint` | 爬取阶段固定 `None`（区划交给 cleaner/geo） |

同一次爬取内按 `id` 去重；达 `max_posts` 停止。

`persist_crawl` 默认写到 `data/raw/crawl_weibo_beijing.jsonl`。

---

## 6. 清洗实现（`cleaner.py`）

版本常量：`LAB1_VERSION = "lab1-crawl4weibo-0.4.0"`。

### 6.1 `normalize_text`

NFKC → 去 URL / @提及 → `#话题#` 保留话题字去 `#` → 去 emoji → 压空白。

### 6.2 丢弃判定顺序与 `drop_reason`

| 顺序 | 条件 | drop_reason |
| --- | --- | --- |
| 1 | `len(clean_text) < 10` | `too_short` |
| 2 | 广告词（点击链接/加微信/扫码…） | `ad_spam` |
| 3 | 小说线索（小说/连载/帝都/繁弦急管…；或「路灯+站在+火星」） | `fiction` |
| 4 | 粉丝噪声（应援/唯粉/花体数字+路灯隐喻…） | `fan_noise` |
| 5 | 政务通稿（见下） | `official_pr` |
| 6 | 非北京（外地线索或无北京锚点且正文不含 query place） | `non_beijing` |
| 7 | 近重指纹已见 | `duplicate` |
| 8 | 无法推断设施 scope | `out_of_scope` |
| 9 | 无汉字 | `no_substance` |

**官方通稿逻辑要点**：

- 命中「接诉即办 / 北京政在说 / 终于亮起来了 / 宣传阐释」等 → 默认丢。  
- **例外保留**：正文含「市民反映 / 有市民 / …」等 **且不含**「已恢复正常 / 值得点赞 / 立即转办 / …」一类办结宣传语。  
- 即：允许保留「引用市民抱怨」的帖；剔除办事结果通稿。

**非北京**：命中邯郸/沈北/青岛合肥路等线索直接丢；否则若正文既无北京锚点（hotspots ∪ district_shorts ∪ 常见区名 ∪「北京」）且不含查询地点 → 丢。

**不去用**微博截断标记 `...全文` 作为小说判定（会误杀真实帖）。

### 6.3 设施与区划

- `infer_facility_scope`：优先 `facility_scope_hint`；否则用 taxonomy labels/symptoms 打分（label 权重 2）。  
- `infer_district`（`geo.py`）：hint 0.95 → POI/geo 地标 0.85 → 正文区名 0.8/0.75 → 正文地标 0.65。  
- 若仍无区划且 `source_query` 能解析出 place，再用地标表回推。

### 6.4 近重

`fingerprint`：去空白标点后 MD5。同 fingerprint 后文丢弃为 `duplicate`。

---

## 7. 契约字段（下游只认这个）

### 7.1 `PostRaw`（raw JSONL 每行）

```json
{
  "id": "wb_...",
  "platform": "weibo",
  "text": "...",
  "time": "2025-12-11T13:00:00+08:00",
  "city": "北京",
  "url": "https://m.weibo.cn/detail/...",
  "author_id_hash": "hex16或null",
  "geo_raw": null,
  "poi": null,
  "district_hint": null,
  "facility_scope_hint": "road_lighting",
  "source_query": "望京路灯不亮"
}
```

### 7.2 `PostCleaned`（cleaned JSONL 每行；正式文件仅 kept）

```json
{
  "id": "wb_...",
  "platform": "weibo",
  "text": "原始正文",
  "clean_text": "规范化正文",
  "time": "...",
  "city": "北京",
  "geo": {
    "raw": "...",
    "poi": "望京",
    "district": "朝阳区",
    "confidence": 0.65
  },
  "meta": {
    "lab1_version": "lab1-crawl4weibo-0.4.0",
    "is_duplicate": false,
    "dropped": false,
    "drop_reason": null,
    "facility_scope_hint": "road_lighting"
  }
}
```

说明：早期设想稿里的 `location/user/is_valid` **不是**运行契约；不要按旧示意改共享 models。

### 7.3 `lab1_cleaning_report.json` 字段

`lab1_version`, `input_count`, `kept_count`, `dropped_count`, `kept_by_scope`, `drop_reasons`, `kept_with_district`, `district_coverage`, `query_plan_size`, `taxonomy_version`, `provenance{...}`。

---

## 8. 怎么使用

### 8.1 环境

```bash
pip install -r requirements.txt
# 含 crawl4weibo、playwright 等
playwright install chromium
```

### 8.2 Cookie（强烈建议）

1. 登录 [weibo.com](https://weibo.com)  
2. F12 → Network → 请求头复制 Cookie  
3. 写入 `secrets/weibo_cookie.txt` **一行**（勿提交 Git）

### 8.3 推荐流程

```bash
# 1) 小规模试爬（每设施 2 个地点查询）
python scripts/run_weibo_crawl.py --smoke --max-posts 40 --delay 3 --run-lab1

# 2) 看报告与样本质量
#    data/cleaned/lab1_cleaning_report.json
#    data/cleaned/beijing_cleaned.jsonl

# 3) 全量（按 taxonomy 查询， cap 帖数）
python scripts/run_weibo_crawl.py --pages 1 --max-posts 600 --delay 3.5 --run-lab1
```

`run_weibo_crawl.py` 主要参数：

| 参数 | 默认 | 含义 |
| --- | --- | --- |
| `--smoke` | off | 精简查询试跑 |
| `--pages` | 1 | 每查询翻页数（建议 1–2） |
| `--delay` | 3.5 | 请求间隔秒 |
| `--max-posts` | 800 | 累计帖数上限 |
| `--max-per-scope` | 28 | 每设施查询条数上限（传给 `build_queries`） |
| `--run-lab1` | off | 爬完后立刻 `run_lab1(source="raw")` |

仅清洗（已有 crawl 文件）：

```bash
python scripts/run_lab1.py --source raw
# 或
python scripts/convert_weibo_to_lab1.py
```

Live 爬（经 Lab1 入口，无文件时才会联网）：

```bash
python scripts/run_lab1.py --source crawl
```

### 8.4 常见失败

| 现象 | 原因 / 处理 |
| --- | --- |
| `CollectionError` / exit 2 | 没有 `crawl_*`/`import_*`，或内容全是 `platform=fixture` |
| 爬到 0 帖 | Cookie/网络/反爬；看 `crawl_weibo_beijing_provenance.json` 的 `errors` |
| kept 全是一路灯 | smoke 时期旧行为；现 smoke 三类设施各 2 place；全量看 `kept_by_scope` |
| 噪声多 | 收紧 taxonomy 查询或扩展 `cleaner` 拒绝词；先 `--smoke` 验质量 |

---

## 9. 与共享层 / 其他 Lab 的边界

| 可改（Lab1） | 不可擅自改 |
| --- | --- |
| `src/lab1_collection/**` | `src/lab2_analysis/**`、`src/lab3_decision/**` |
| `configs/keywords_taxonomy.yaml` | `configs/need_mapping.yaml` |
| `scripts/run_lab1.py`、`run_weibo_crawl.py`… | `src/common/models.py` 字段（需 SHARED） |
| Lab1 测试 | 假装数据冒充演示集 |

下游：Lab2 读 `data/cleaned/beijing_cleaned.jsonl`；应容忍部分 `geo.district=null`（Lab3 会把空区划打成 `未定位/全市`）。

---

## 10. 实现与课程叙事的对应（便于答辩）

| 课程关注点 | 代码落点 |
| --- | --- |
| 关键词覆盖设施×问题×地点 | `keywords_taxonomy.yaml` + `build_queries` 紧拼查询 |
| 沉默需求暗示表达 | `need_cues` → `place_need` 层查询 |
| 持续采样而非灾害突发 | 多查询窄检索 + delay；非事件触发单次爆破 |
| 清洗去重去噪 | `cleaner.normalize/fingerprint` + fiction/fan/official/non_beijing |
| 空间可聚合 | `geo.infer_district` → `PostCleaned.geo.district` |
| 真数据纪律 | `sources.CollectionError`，无 fixture 回退 |

---

## 11. 版本备忘

| 项 | 当前值 |
| --- | --- |
| Lab1 cleaner 版本串 | `lab1-crawl4weibo-0.4.0` |
| Taxonomy | `version: 4` |
| 爬虫库 | `crawl4weibo`（见根目录 `requirements.txt`） |
| 文档同步日期 | 2026-07-15 |

以后改查询策略、丢弃规则或落盘文件名时：**先改代码/配置，再改本文同一提交**，避免文档漂。
