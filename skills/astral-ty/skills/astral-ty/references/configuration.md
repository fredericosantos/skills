# Configuration Examples

## Basic pyproject.toml Configuration

```toml
[tool.ty.environment]
python-version = "3.12"

[tool.ty.rules]
possibly-unresolved-reference = "warn"
division-by-zero = "error"
unresolved-import = "error"

[tool.ty.src]
include = ["src/**/*.py"]
exclude = ["**/migrations/**", "**/tests/**"]

[tool.ty.terminal]
output-format = "full"
error-on-warning = false
```

## Strict Configuration

```toml
[tool.ty.environment]
python-version = "3.12"

[tool.ty.rules]
possibly-unresolved-reference = "error"
division-by-zero = "error"
unresolved-import = "error"
unresolved-attribute = "error"
invalid-argument = "error"

[tool.ty.terminal]
error-on-warning = true
```

## Per-File Overrides

### Different Rules for Tests

```toml
[[tool.ty.overrides]]
include = ["tests/**", "**/test_*.py"]

[tool.ty.overrides.rules]
possibly-unresolved-reference = "warn"  # Allow test-specific patterns
unresolved-import = "ignore"            # Tests may import private modules
```

### Relaxed Rules for Scripts

```toml
[[tool.ty.overrides]]
include = ["scripts/**", "**/manage.py"]

[tool.ty.overrides.rules]
possibly-unresolved-reference = "warn"
unresolved-import = "warn"
```