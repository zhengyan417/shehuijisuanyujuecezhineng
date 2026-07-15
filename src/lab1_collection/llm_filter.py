"""LLM semantic gate for Lab1 keep/drop (NVIDIA API).

OWNER: AGENT_LAB1

No keyword blacklists. Default fast model: nemotron-mini-4b.
Refine pass recommendation: meta/llama-3.1-8b-instruct (slightly better, still fast).
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src.common.models import FacilityScope, PostCleaned
from src.common.paths import CLEANED, ensure_data_dirs

DEFAULT_MODEL = os.getenv("LAB1_LLM_MODEL", "nvidia/nemotron-mini-4b-instruct")
REFINE_MODEL = os.getenv("LAB1_LLM_REFINE_MODEL", "meta/llama-3.1-8b-instruct")
NVIDIA_BASE = os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")
CACHE_NAME = "llm_filter_cache.jsonl"
REFINE_CACHE_NAME = "llm_refine_cache.jsonl"

_SYSTEM = """你是北京公共设施数据质检员。判断微博是否 KEEP。

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
"""


def _api_key() -> str:
    key = (os.getenv("NVIDIA_API_KEY") or os.getenv("NGC_API_KEY") or "").strip()
    if not key:
        raise RuntimeError("NVIDIA_API_KEY not set")
    return key


def _chat(user_content: str, model: str, *, max_tokens: int = 1200, timeout: int = 60) -> str:
    payload = {
        "model": model,
        "temperature": 0,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user_content},
        ],
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        f"{NVIDIA_BASE.rstrip('/')}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return (data["choices"][0]["message"].get("content") or "").strip()


def _extract_json_list(content: str) -> list[dict]:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    m = re.search(r"\[.*\]", content, flags=re.S)
    if m:
        try:
            arr = json.loads(m.group(0))
            if isinstance(arr, list):
                return [x for x in arr if isinstance(x, dict)]
        except json.JSONDecodeError:
            pass
    m2 = re.search(r"\{.*\}", content, flags=re.S)
    if m2:
        try:
            obj = json.loads(m2.group(0))
            if isinstance(obj, dict):
                return [obj]
        except json.JSONDecodeError:
            pass
    return []


def _valid_scope(value) -> FacilityScope | None:
    if value in ("road_lighting", "public_charging", "public_transit"):
        return value  # type: ignore[return-value]
    return None


def _as_bool(value, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return default


def _normalize_row(row: dict, fallback_id: str | None = None) -> dict:
    pid = str(row.get("id") or fallback_id or "").strip()
    keep = _as_bool(row.get("keep"), False)
    mediated = _as_bool(row.get("is_mediated"), False)
    scope = _valid_scope(row.get("facility_scope"))
    if scope is None:
        blob = json.dumps(row, ensure_ascii=False)
        for cand in ("road_lighting", "public_charging", "public_transit"):
            if cand in blob:
                scope = cand  # type: ignore[assignment]
                break
    return {
        "id": pid,
        "keep": keep,
        "is_mediated": mediated and keep,
        "reason": str(row.get("reason") or ("keep" if keep else "drop"))[:120],
        "facility_scope": scope,
        "ok": True,
    }


def judge_batch(
    items: list[dict],
    *,
    model: str = DEFAULT_MODEL,
    retries: int = 4,
) -> list[dict]:
    """items: [{id,text,geo_raw,poi,district}, ...]."""
    if not items:
        return []
    lines = []
    for it in items:
        t = (it.get("text") or "").replace("\n", " ")[:320]
        lines.append(
            "- id={id}\n  geo_raw={geo_raw}\n  poi={poi}\n  district={district}\n  text={text}".format(
                id=it.get("id"),
                geo_raw=it.get("geo_raw") or "",
                poi=it.get("poi") or "",
                district=it.get("district") or "",
                text=t,
            )
        )
    user = "请对下列微博逐条判断，返回等长JSON数组：\n" + "\n".join(lines)

    last_err = None
    for i in range(retries):
        try:
            raw = _chat(user, model=model, max_tokens=min(150 * len(items) + 250, 2000))
            arr = _extract_json_list(raw)
            by_id = {}
            for obj in arr:
                row = _normalize_row(obj)
                if row["id"]:
                    by_id[row["id"]] = row
            out = []
            for it in items:
                pid = str(it.get("id"))
                if pid in by_id:
                    out.append(by_id[pid])
                elif len(items) == 1 and arr:
                    out.append(_normalize_row(arr[0], fallback_id=pid))
                else:
                    out.append(
                        {
                            "id": pid,
                            "keep": None,
                            "is_mediated": False,
                            "reason": "llm_missing_item",
                            "facility_scope": None,
                            "ok": False,
                        }
                    )
            if sum(1 for r in out if r.get("ok")) == 0:
                raise RuntimeError("no valid items parsed")
            return out
        except urllib.error.HTTPError as e:
            last_err = e
            wait = 2.0 * (i + 1)
            if e.code in {429, 503, 502}:
                wait = 4.0 * (i + 1)
            time.sleep(wait)
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1.2 * (i + 1))

    return [
        {
            "id": str(it.get("id")),
            "keep": None,
            "is_mediated": False,
            "reason": f"llm_error:{type(last_err).__name__}",
            "facility_scope": None,
            "ok": False,
        }
        for it in items
    ]


def judge_one(text: str, *, model: str = DEFAULT_MODEL, retries: int = 4) -> dict:
    rows = judge_batch([{"id": "x", "text": text}], model=model, retries=retries)
    return rows[0] if rows else {"keep": None, "reason": "llm_error", "ok": False}


def cache_path(name: str = CACHE_NAME) -> Path:
    ensure_data_dirs()
    return CLEANED / name


def load_cache(path: Path | None = None, *, include_errors: bool = False) -> dict[str, dict]:
    p = path or cache_path()
    out: dict[str, dict] = {}
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        pid = row.get("id")
        if not pid:
            continue
        reason = str(row.get("reason") or "")
        if (not include_errors) and (row.get("ok") is False or reason.startswith("llm_error")):
            continue
        out[str(pid)] = row
    return out


def rewrite_cache(rows: dict[str, dict], path: Path | None = None) -> None:
    p = path or cache_path()
    ensure_data_dirs()
    with p.open("w", encoding="utf-8") as f:
        for row in rows.values():
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def append_cache(rows: list[dict], path: Path | None = None) -> None:
    p = path or cache_path()
    with p.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _post_payload(p: PostCleaned) -> dict:
    return {
        "id": p.id,
        "text": p.text or p.clean_text,
        "geo_raw": p.geo.raw,
        "poi": p.geo.poi,
        "district": p.geo.district,
    }


def _apply_decision(post: PostCleaned, row: dict) -> None:
    keep = bool(row["keep"])
    post.meta.dropped = not keep
    post.meta.drop_reason = None if keep else f"llm:{row.get('reason', 'drop')}"
    mediated = bool(row.get("is_mediated")) and keep
    # B类硬标记：保留且正文含转述线索
    blob = post.text or post.clean_text or ""
    if keep and any(k in blob for k in ("市民反映", "有市民", "居民反映", "网友反映", "家长反映")):
        mediated = True
    post.meta.is_mediated = mediated
    scope = _valid_scope(row.get("facility_scope"))
    if scope:
        post.meta.facility_scope_hint = scope


def apply_llm_filter(
    cleaned: list[PostCleaned],
    *,
    model: str = DEFAULT_MODEL,
    workers: int = 6,
    batch_size: int = 8,
    resume: bool = True,
    cache_file: str = CACHE_NAME,
    only_undropped: bool = False,
) -> list[PostCleaned]:
    cpath = cache_path(cache_file)
    cache = load_cache(cpath) if resume else {}
    if resume:
        rewrite_cache(cache, cpath)

    pending: list[PostCleaned] = []
    for c in cleaned:
        if c.meta.dropped and c.meta.drop_reason in {"too_short", "duplicate"}:
            continue
        if only_undropped and c.meta.dropped:
            continue
        if c.meta.dropped and str(c.meta.drop_reason or "").startswith("llm:llm_error"):
            c.meta.dropped = False
            c.meta.drop_reason = None
        if c.meta.dropped and not only_undropped:
            # keep previous non-error drop unless we're refining kept-only
            continue
        if c.id in cache:
            decision = cache[c.id]
            if decision.get("ok") is False or decision.get("keep") is None:
                pending.append(c)
                continue
            _apply_decision(c, decision)
            continue
        pending.append(c)

    print(
        f"[llm_filter] model={model} workers={workers} batch={batch_size} "
        f"cache={cache_file} pending={len(pending)}",
        flush=True,
    )

    batches = [pending[i : i + batch_size] for i in range(0, len(pending), batch_size)]
    done_items = 0
    fail_items = 0
    new_rows: list[dict] = []

    def _job(batch: list[PostCleaned]) -> list[tuple[PostCleaned, dict]]:
        payload = [_post_payload(p) for p in batch]
        decisions = judge_batch(payload, model=model)
        by_id = {d["id"]: d for d in decisions}
        return [
            (p, by_id.get(p.id) or {"id": p.id, "ok": False, "keep": None, "reason": "missing"})
            for p in batch
        ]

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futs = [pool.submit(_job, b) for b in batches]
        for fut in as_completed(futs):
            pairs = fut.result()
            for post, row in pairs:
                done_items += 1
                if not row.get("ok") or row.get("keep") is None:
                    fail_items += 1
                    continue
                _apply_decision(post, row)
                new_rows.append(
                    {
                        "id": post.id,
                        "keep": bool(row["keep"]),
                        "is_mediated": bool(row.get("is_mediated")),
                        "reason": row.get("reason"),
                        "facility_scope": row.get("facility_scope"),
                        "ok": True,
                    }
                )
            if len(new_rows) >= 20:
                append_cache(new_rows, cpath)
                new_rows = []
            print(
                f"[llm_filter] progress items={done_items}/{len(pending)} fails={fail_items}",
                flush=True,
            )

    if new_rows:
        append_cache(new_rows, cpath)
    if fail_items:
        print(
            f"[llm_filter] WARNING {fail_items} unresolved (left undropped). Re-run to resume.",
            flush=True,
        )
    return cleaned


def refine_kept(
    cleaned: list[PostCleaned],
    *,
    model: str = REFINE_MODEL,
    workers: int = 6,
    batch_size: int = 6,
) -> list[PostCleaned]:
    """Second-pass: only re-judge currently kept rows with a stronger-but-fast model."""
    for c in cleaned:
        if not c.meta.dropped:
            # force re-judge
            pass
    return apply_llm_filter(
        cleaned,
        model=model,
        workers=workers,
        batch_size=batch_size,
        resume=True,
        cache_file=REFINE_CACHE_NAME,
        only_undropped=True,
    )
