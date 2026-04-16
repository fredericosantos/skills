# Scoping

Apply `__init__.py` docstrings only to **your project's own packages**. On
first use, ask the user which directories to manage.

Do NOT apply to:
- Third-party code (`site-packages`, `.venv`, `venv`)
- Vendored code (`vendor/`, `vendored/`, `third_party/`)
- Git submodules, `__pycache__`, `.git`, `node_modules`
- Any directory in `.gitignore`

This documents **file structure**, not public API. It complements `__all__` —
the docstring shows what files exist and what they contain, while `__all__`
controls import behavior.
