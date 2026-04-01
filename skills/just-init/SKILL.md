---
name: just-init
description: "Navigate and document Python packages using __init__.py docstrings as living indexes: read them before exploring, update them after every file change."
---

# just-init

Use `__init__.py` docstrings as the single source of truth for navigating and
documenting Python packages.

## Read Rule

When navigating to a new directory in the codebase, read its `__init__.py` to
understand the package. The docstring tree tells you what's inside and where.

Subdirectory entries include `[start:end]` — the line range of that directory's
`__init__.py` docstring. Use these as offset and limit to read only the
docstring, not the entire file. This eliminates extra tool calls.

## Docstring Format

Every `__init__.py` must start with a triple-quoted docstring:

```python
"""
One-line description of what this package does.

package_name/
├── __init__.py        # Package init and public exports.
├── subpackage/        # Brief description of subpackage. [1:15]
├── module_a.py        # Brief description of module_a.
└── module_b.py        # Brief description of module_b.
    ├── ClassA          # Does something. [10:50]
    └── func_b          # Does something else. [52:80]
"""
```

Rules:
- `├──` for all entries except the last (`└──`).
- Subdirectories first (alphabetical), then `.py` files (alphabetical).
- Subdirectories end with `/`, not expanded. `[start:end]` = their `__init__.py` docstring lines.
- Files with 3+ public definitions get sub-entries with `description [start:end]`.
- Descriptions under 10 words. Package name matches the directory name.

## Update Rule

After any file or directory add, remove, or rename — update the `__init__.py`
docstring. New package: create `__init__.py` first. Propagate changes to parent
if a sub-package entry changed.

Missing or outdated docstring: fix it before proceeding.

## Automation

`uv run scripts/just-init.py <generate|verify|update> <path>` — see
[automation](references/automation.md) for modes, options, and hook setup.

## References

- [Scoping](references/scoping.md) — when to apply, what to skip
- [Automation](references/automation.md) — script modes and Claude Code hook
- [Line index](references/line-index.md) — line-range sub-entry details
- [Flat package](references/flat-package.md)
- [Nested packages](references/nested-packages.md)
- [Non-Python directories](references/non-python-dirs.md)
- [Update: adding a file](references/update-add-file.md)
- [Update: adding a sub-package](references/update-add-subpackage.md)
