---
name: No __init__.py in test directories
description: Do not create __init__.py files in test directories — project uses pytest importlib import mode
type: feedback
---

Do not create `__init__.py` files in test directories (`test/`, `test/test_ingestion/`, etc.).

**Why:** The project uses pytest's `importlib` import mode (`--import-mode=importlib`), which does not require `__init__.py` for test discovery. Per pytest best practices (https://docs.pytest.org/en/7.1.x/explanation/goodpractices.html), these files are unnecessary and add noise.

**How to apply:** When creating test subdirectories, use `mkdir` only — no `__init__.py`. If generating test files, do not prepend an `__init__.py` step.
