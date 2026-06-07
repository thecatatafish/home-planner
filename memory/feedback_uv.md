---
name: feedback-uv
description: User prefers UV for Python dependency management, not pip
metadata:
  type: feedback
---

Use `uv` for all Python dependency management in this project. Do not use `pip install` or `pip` directly.

**Why:** User preference — they use UV on their homelab.

**How to apply:** Use `uv add` to add dependencies, `uv run` to run scripts, `uv sync` to install deps. Generate `pyproject.toml` instead of or in addition to `requirements.txt`.
