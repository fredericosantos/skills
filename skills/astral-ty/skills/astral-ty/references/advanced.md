# Advanced Configuration

## Multiple Python Versions

```bash
# Check against multiple versions
ty check --python-version 3.11
ty check --python-version 3.12
```

## Custom Include/Exclude Patterns

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