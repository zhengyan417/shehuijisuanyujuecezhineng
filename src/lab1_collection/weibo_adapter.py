"""Convert dataabc/weibo-search CSV outputs into Lab1 PostRaw JSONL.

OWNER: AGENT_LAB1
"""

from __future__ import annotations

import csv
import hashlib
import re
from datetime import datetime
from pathlib import Path

from src.common.io import dump_models, write_jsonl
from src.common.models import FacilityScope, PostRaw
from src.common.paths import RAW, ROOT, ensure_data_dirs
from src.lab1_collection.cleaner import infer_facility_scope

WEIBO_SEARCH_ROOT = ROOT / "third_party" / "weibo-search"
RESULT_ROOT = WEIBO_SEARCH_ROOT / "结果文件"


def _hash_user(user_id: str) -> str | None:
    uid = (user_id or "").strip()
    if not uid:
        return None
    return hashlib.sha256(uid.encode("utf-8")).hexdigest()[:16]


def _parse_time(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return datetime.now().astimezone().isoformat(timespec="seconds")
    # weibo-search typically writes yyyy-mm-dd
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(value, fmt)
            return dt.astimezone().isoformat(timespec="seconds") if dt.tzinfo else dt.isoformat(timespec="seconds")
        except ValueError:
            continue
    return value


def _clean_weibo_text(text: str) -> str:
    text = text or ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _guess_scope(keyword: str, text: str) -> FacilityScope | None:
    blob = f"{keyword} {text}"
    return infer_facility_scope(blob, None)


def iter_csv_rows(result_root: Path = RESULT_ROOT):
    if not result_root.exists():
        return
    for csv_path in sorted(result_root.rglob("*.csv")):
        keyword = csv_path.stem
        with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield keyword, row


def convert_weibo_csvs(
    result_root: Path = RESULT_ROOT,
    output_name: str = "crawl_weibo_beijing.jsonl",
) -> Path:
    ensure_data_dirs()
    posts: list[PostRaw] = []
    seen: set[str] = set()

    for keyword, row in iter_csv_rows(result_root) or ():
        wid = str(row.get("id") or row.get("bid") or "").strip()
        text = _clean_weibo_text(row.get("微博正文") or row.get("text") or "")
        if not wid or not text:
            continue
        if wid in seen:
            continue
        seen.add(wid)

        loc = (row.get("发布位置") or "").strip() or None
        scope = _guess_scope(keyword, text)
        created = (row.get("发布时间") or "").strip()
        if created and len(created) == 10:
            time_iso = f"{created}T12:00:00+08:00"
        else:
            time_iso = _parse_time(created)

        posts.append(
            PostRaw(
                id=f"wb_{wid}",
                platform="weibo",
                text=text,
                time=time_iso,
                city="北京",
                url=f"https://m.weibo.cn/detail/{wid}" if wid.isdigit() else None,
                author_id_hash=_hash_user(str(row.get("user_id") or "")),
                geo_raw=loc,
                poi=loc,
                district_hint=None,
                facility_scope_hint=scope,
                source_query=keyword,
            )
        )

    if not posts:
        raise FileNotFoundError(
            f"No convertible Weibo CSV rows under {result_root}. Run scripts/run_weibo_crawl.py first."
        )

    out = RAW / output_name
    write_jsonl(out, dump_models(posts))
    return out


if __name__ == "__main__":
    path = convert_weibo_csvs()
    print(f"[convert] wrote {path}")
