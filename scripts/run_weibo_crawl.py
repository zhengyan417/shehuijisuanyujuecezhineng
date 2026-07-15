#!/usr/bin/env python
"""Run vendored dataabc/weibo-search for Beijing facility keywords.

OWNER: AGENT_LAB1

Requires Weibo cookie in one of:
  - env WEIBO_COOKIE
  - secrets/weibo_cookie.txt

Usage:
  python scripts/run_weibo_crawl.py
  python scripts/run_weibo_crawl.py --start 2026-06-01 --end 2026-07-15 --limit 80
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEIBO_ROOT = ROOT / "third_party" / "weibo-search"
KEYWORDS = ROOT / "configs" / "weibo_keywords.txt"
COOKIE_FILE = ROOT / "secrets" / "weibo_cookie.txt"


def load_cookie() -> str:
    env = os.getenv("WEIBO_COOKIE", "").strip()
    if env:
        return env
    if COOKIE_FILE.exists():
        text = COOKIE_FILE.read_text(encoding="utf-8").strip()
        lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
        if lines:
            return lines[0]
    raise SystemExit(
        "Missing Weibo cookie.\n"
        "1) Copy secrets/weibo_cookie.txt.example -> secrets/weibo_cookie.txt\n"
        "2) Paste Cookie from weibo.com/weibo.cn after login\n"
        "3) Re-run: python scripts/run_weibo_crawl.py"
    )


def load_keywords() -> list[str]:
    lines = KEYWORDS.read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2026-06-01", help="START_DATE yyyy-mm-dd")
    parser.add_argument("--end", default="2026-07-15", help="END_DATE yyyy-mm-dd")
    parser.add_argument("--limit", type=int, default=80, help="LIMIT_RESULT per run (0=unlimited)")
    parser.add_argument("--delay", type=int, default=8, help="DOWNLOAD_DELAY seconds")
    parser.add_argument("--region", default="北京", help="REGION filter")
    args = parser.parse_args()

    if not WEIBO_ROOT.exists():
        raise SystemExit(f"Missing vendored crawler: {WEIBO_ROOT}")
    if not KEYWORDS.exists():
        raise SystemExit(f"Missing keyword file: {KEYWORDS}")

    keywords = load_keywords()
    if not keywords:
        raise SystemExit(f"No keywords in {KEYWORDS}")

    cookie = load_cookie()
    env = os.environ.copy()
    env["WEIBO_COOKIE"] = cookie
    env["WEIBO_KEYWORDS"] = json.dumps(keywords, ensure_ascii=False)
    env["WEIBO_REGION"] = json.dumps([args.region], ensure_ascii=False)
    env["WEIBO_START_DATE"] = args.start
    env["WEIBO_END_DATE"] = args.end
    env["WEIBO_LIMIT_RESULT"] = str(args.limit)
    env["WEIBO_TYPE"] = "1"
    env["WEIBO_CONTAIN_TYPE"] = "0"
    env["WEIBO_FURTHER_THRESHOLD"] = "46"

    cmd = [
        sys.executable,
        "-m",
        "scrapy",
        "crawl",
        "search",
        "-s",
        f"DOWNLOAD_DELAY={args.delay}",
        "-s",
        "LOG_LEVEL=INFO",
        "-s",
        "JOBDIR=crawls/beijing_silent_demand",
    ]
    print("[crawl] cwd=", WEIBO_ROOT)
    print("[crawl] keywords=", len(keywords), keywords[:3], "...")
    print("[crawl] region=", args.region, "range=", args.start, "->", args.end, "limit=", args.limit)
    proc = subprocess.run(cmd, cwd=str(WEIBO_ROOT), env=env)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)
    print("[crawl] done. Next: python scripts/convert_weibo_to_lab1.py --run-lab1")


if __name__ == "__main__":
    main()
