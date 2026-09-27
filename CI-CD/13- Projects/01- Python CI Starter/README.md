# 01 - Python CI Starter

A minimal runnable Python project that demonstrates checkout, Python setup,
dependency installation, pytest, coverage, permissions, and pull-request CI.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install pytest pytest-cov
pytest -q
```

## GitHub Actions concepts

- Workflow triggers
- `permissions`
- `actions/checkout`
- `actions/setup-python`
- Dependency caching
- Test execution
- Coverage
