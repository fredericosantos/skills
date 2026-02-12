# ty Examples

## Basic Type Checking

### Check All Files

```bash
# Check all Python files in current directory
ty check

# Check specific file
ty check my_module.py

# Check specific directory
ty check src/
```

### Configure Rule Levels

```bash
# Treat unresolved references as errors
ty check --error possibly-unresolved-reference

# Treat division by zero as warnings
ty check --warn division-by-zero

# Ignore unresolved imports
ty check --ignore unresolved-import
```

## Python Version Targeting

### Target Specific Python Versions

```bash
# Check against Python 3.12
ty check --python-version 3.12

# Check against Python 3.11
ty check --python-version 3.11
```

### Platform-Specific Checking

```bash
# Target Linux platform
ty check --python-platform linux

# Target Windows platform
ty check --python-platform windows
```

## Configuration Examples

### Basic pyproject.toml Configuration

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

### Strict Configuration

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

## Migration Examples

### From mypy

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

### From Pyright

```bash
# Old workflow
pyright .
pyright --pythonversion 3.12 src/

# New workflow
ty check
ty check --python-version 3.12 src/
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Type check with ty
  run: |
    uvx ty check
    uvx ty check --error-on-warning tests/
```

### Pre-commit Hook

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

## Advanced Configuration

### Multiple Python Versions

```bash
# Check against multiple versions
ty check --python-version 3.11
ty check --python-version 3.12
```

### Custom Include/Exclude Patterns

```toml
[tool.ty.src]
include = [
    "src/**/*.py",
    "lib/**/*.py",
    "!**/generated/**",  # Exclude generated files
]
exclude = [
    "**/migrations/**",
    "**/tests/**",
    "**/__pycache__/**",
]
```

## Error Handling Examples

### Proper Ignore Comments

```python
# Correct: Rule-specific ignore
from typing import Any
x: Any = get_unknown_value()  # ty: ignore[possibly-unresolved-reference]

# Incorrect: Blanket ignore
x = undefined_var  # ty: ignore

# Incorrect: Generic type ignore
x = undefined_var  # type: ignore
```

### Common Error Patterns

```python
# Division by zero detection
def divide(a: int, b: int) -> float:
    return a / b  # ty will warn about potential division by zero

# Better: Handle the case
def divide(a: int, b: int) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

## IDE Integration

### VS Code Settings

```json
{
  "python.languageServer": "ty",
  "python.analysis.typeCheckingMode": "basic",
  "ty.server.enabled": true
}
```

### Language Server Features

ty provides:
- Real-time type checking
- Go to definition
- Find references
- Hover information
- Auto-completion
- Import suggestions