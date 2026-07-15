# 北京市公共资源「沉默需求」发现流水线

课程项目框架：社交媒体信号 → 清洗 → 意图/情绪/需求映射 → 生成式决策支持。

**范围冻结**

- 城市：北京
- 主题：道路照明 / 公共充电设施 / 公共交通设施（公交站/天桥）

## Coding agents start here

1. `AGENTS.md`
2. `collab/00_READ_THIS_FIRST.md`
3. `collab/MODULE_OWNERS.md`
4. Role guide under `collab/guides/`
5. Paste prompts from `collab/AGENT_PROMPTS.md`

Humans mainly assign roles in `collab/ROLE_CLAIM.md` and open the remote git later.

## Quickstart

```bash
python -m pip install -r requirements.txt
python scripts/run_pipeline.py
python -m pytest -q
```

Offline fixture path is default when `data/raw/` has no crawl outputs.

### Real Weibo crawl (Lab1)

Vendored crawler: `third_party/weibo-search` = [dataabc/weibo-search](https://github.com/dataabc/weibo-search)

```bash
pip install -r requirements.txt
# put Cookie into secrets/weibo_cookie.txt
python scripts/run_weibo_crawl.py
python scripts/convert_weibo_to_lab1.py --run-lab1
```

See `third_party/README_weibo_search.md`.

## Layout

```text
src/lab1_collection   # AGENT_LAB1
src/lab2_analysis     # AGENT_LAB2
src/lab3_decision     # AGENT_LAB3
src/common            # SHARED contract models
configs/              # taxonomy + mapping
schemas/              # JSON schemata mirroring pydantic
collab/               # multi-agent collaboration protocol
fixtures/             # reproducible samples
```

## Remote git

When repository URL is provided, connect with:

```bash
git remote add origin <URL>
git push -u origin main
```

Then each teammate clones, claims a role, and starts from `collab/AGENT_PROMPTS.md`.
