# ruff Examples

## Basic Linting and Formatting

### Check All Files

```bash
# Check for linting issues
ruff check .

# Check specific file
ruff check my_script.py
```

### Auto-Fix Issues

```bash
# Fix safe issues automatically
ruff check --fix .

# Preview unsafe fixes first
ruff check --fix --unsafe-fixes --diff .

# Apply unsafe fixes
ruff check --fix --unsafe-fixes .
```

### Format Code

```bash
# Format all files
ruff format .

# Check if files need formatting
ruff format --check .

# Preview formatting changes
ruff format --diff .
```

## Configuration Examples

### Basic pyproject.toml Configuration

```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "N", "B"]
ignore = ["E501"]  # Line too long

[tool.ruff.lint.isort]
known-first-party = ["myproject"]
```

### Strict Configuration

```toml
[tool.ruff.lint]
select = ["ALL"]
ignore = [
    "COM812",  # Trailing comma missing
    "ISC001",  # Implicitly concatenated string literals
    "T10",     # Debugger statements
    "T20",     # Print statements
]
```

## Rule-Specific Examples

### Import Sorting

```bash
# Check only import sorting
ruff check --select I .

# Fix import sorting
ruff check --select I --fix .
```

### Python Version Upgrades

```bash
# Check for outdated syntax
ruff check --select UP .

# Upgrade syntax automatically
ruff check --select UP --fix .
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Lint with ruff
  run: |
    ruff check .
    ruff format --check .

- name: Fix with ruff
  run: |
    ruff check --fix .
    ruff format .
```

### Pre-commit Hook

```yaml
repos:
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

## Migration Examples

### From Black + Flake8 + isort

```bash
# Old workflow
black .
flake8 .
isort .

# New workflow
ruff check --fix .
ruff format .
```

### From autopep8 + flake8

```bash
# Old workflow
autopep8 --in-place --aggressive --aggressive .
flake8 .

# New workflow
ruff check --fix .
ruff format .
```

## Selective Rule Enforcement

### Check Only Specific Rules

```bash
# Only check syntax errors and undefined names
ruff check --select E,F .

# Check everything except style issues
ruff check --select "ALL" --ignore "E,W"
```

### Per-File Overrides

```toml
[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["B011", "S101"]  # assert False, assert used
"scripts/**/*.py" = ["T201"]        # print found
```

## Advanced Usage

### Watching for Changes

```bash
# Watch mode for development
ruff check --watch .
```

### Explain Rules

```bash
# Understand why a rule exists
ruff rule F401  # Module imported but unused
ruff rule E501  # Line too long
```

### Custom Rule Selection

```bash
# Enable additional rule categories
ruff check --select "E,F,I,UP,B" .

# Disable specific rules
ruff check --ignore "E501,F401" .
```