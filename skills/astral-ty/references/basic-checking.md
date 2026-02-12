# Basic Type Checking

## Check All Files

```bash
# Check all Python files in current directory
ty check

# Check specific file
ty check my_module.py

# Check specific directory
ty check src/
```

## Configure Rule Levels

```bash
# Treat unresolved references as errors
ty check --error possibly-unresolved-reference

# Treat division by zero as warnings
ty check --warn division-by-zero

# Ignore unresolved imports
ty check --ignore unresolved-import
```