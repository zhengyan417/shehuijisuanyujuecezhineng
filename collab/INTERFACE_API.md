# INTERFACE_API — callable boundaries

Downstream code should import these functions only.

## Lab1

```python
from src.lab1_collection.collector import run_lab1, load_raw_posts, clean_posts
```

- `run_lab1(output_name="beijing_cleaned.jsonl") -> str`
- side effect: writes cleaned JSONL

## Lab2

```python
from src.lab2_analysis.analyzer import run_lab2, analyze_posts
```

- `run_lab2(input_name="beijing_cleaned.jsonl", output_name="beijing_analyzed.jsonl") -> str`

## Lab3

```python
from src.lab3_decision.report import run_lab3, aggregate, render_markdown
```

- `run_lab3(input_name="beijing_analyzed.jsonl", report_stem="beijing_silent_demand") -> str`

## Pipeline

```python
from src.pipeline import run_all
```

- `run_all() -> dict[str,str]` with keys cleaned/analyzed/report

## Compatibility rule

If changing function signatures, keep kwargs defaults stable or provide wrappers in the same release.
