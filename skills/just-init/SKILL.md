---
name: just-init
description: "Navigate and document Python packages using __init__.py docstrings as living indexes: read them before exploring, update them after every file change."
---

# just-init

Use `__init__.py` docstrings as the single source of truth for navigating and
documenting Python packages.

## Read Rule

When navigating to a new directory in the codebase, first extract its
`__init__.py` docstring to understand the package:

1. `grep -nE "^(\"\"\"|''')" <file> | head -2` to get the opening and closing line numbers.
2. Read the file with those line numbers as offset (start line) and limit (number of lines).

Use the docstring tree to decide which files to explore next. Apply recursively
when entering sub-packages.

## Docstring Format

Every `__init__.py` must start with a triple-quoted docstring:

```python
"""
One-line description of what this package does.

package_name/
├── __init__.py        # Package init and public exports.
├── module_a.py        # Brief description of module_a.
├── module_b.py        # Brief description of module_b.
└── subpackage/        # Brief description of subpackage.
"""
```

Rules:
- `├──` for all entries except the last (`└──`).
- `.py` files first (alphabetical), then subdirectories (alphabetical).
- Subdirectories end with `/` and are not expanded here.
- Descriptions under 10 words. Package name matches the directory name.
- Non-Python directories (data, fixtures): list with trailing `/`, no `__init__.py`.

## Update Rule

After any file or directory add, remove, or rename inside a package,
immediately update the affected `__init__.py` docstring. When creating a new
package, create `__init__.py` with its docstring first, then add other files.

Propagate changes: update both the sub-package's `__init__.py` and the parent's
if the sub-package entry changed.

**Missing docstring**: when encountering an `__init__.py` without a docstring,
generate one from the current directory contents before proceeding.

**Outdated docstring**: if the docstring does not match actual files, update it
to reflect reality before continuing.

## References

- [Flat package](references/flat-package.md)
- [Nested packages](references/nested-packages.md)
- [Non-Python directories](references/non-python-dirs.md)
- [Update: adding a file](references/update-add-file.md)
- [Update: adding a sub-package](references/update-add-subpackage.md)
