"""Lab1 Weibo crawl via vendored dataabc/weibo-search.

SOURCE REPO: https://github.com/dataabc/weibo-search
LOCAL PATH: third_party/weibo-search

## Why this repo
- Keyword search crawler (fits Lab1 taxonomy queries)
- Supports REGION=北京
- Actively used for academic/course Weibo collection

## One-time setup
1. pip install -r third_party/weibo-search/requirements.txt
2. Copy secrets/weibo_cookie.txt.example -> secrets/weibo_cookie.txt
3. Login weibo.com, F12 copy Cookie into secrets/weibo_cookie.txt

## Crawl -> Lab1
```bash
python scripts/run_weibo_crawl.py --start 2026-06-01 --end 2026-07-15 --limit 80
python scripts/convert_weibo_to_lab1.py --run-lab1
```

Outputs:
- third_party/weibo-search/结果文件/**/*.csv
- data/raw/crawl_weibo_beijing.jsonl
- data/cleaned/beijing_cleaned.jsonl

## Notes
- Cookie is required (Weibo blocks anonymous search APIs as of 2026).
- Never commit secrets/weibo_cookie.txt
- Keep DOWNLOAD_DELAY >= 8 to reduce ban risk
- For course demo without cookie, fixture mode still works
"""
