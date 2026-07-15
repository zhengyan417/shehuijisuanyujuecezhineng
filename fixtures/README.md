FORBIDDEN — do not put fake social-media sample posts here.

Team policy: 绝对禁止假数据。没有真实爬取/导入数据就不跑 Lab1/2/3。

Real data locations only:
- data/raw/crawl_*.jsonl  (from scripts/run_weibo_crawl.py + convert)
- data/raw/import_*.jsonl (manual real exports)

To crawl:
1. secrets/weibo_cookie.txt
2. python scripts/run_weibo_crawl.py
3. python scripts/convert_weibo_to_lab1.py
