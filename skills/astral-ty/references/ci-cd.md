# CI/CD Integration

## GitHub Actions Example

```yaml
- name: Type check with ty
  run: |
    uvx ty check
    uvx ty check --error-on-warning tests/
```

## Pre-commit Hook

```yaml
repos:
  - repo: local
    hooks:
      - id: ty
        name: ty
        entry: uvx ty check
        language: system
        pass_filenames: false
        files: \.py$
```