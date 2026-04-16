# Migration Examples

## From mypy

```bash
# Old workflow
mypy .
mypy --strict src/
mypy --ignore-missing-imports tests/

# New workflow
ty check
ty check src/
ty check --ignore unresolved-import tests/
```

## From Pyright

```bash
# Old workflow
pyright .
pyright --pythonversion 3.12 src/

# New workflow
ty check
ty check --python-version 3.12 src/
```