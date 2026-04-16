# Line Index

Files with 3+ public top-level definitions include a line-range index.
Subdirectories include `[start:end]` pointing to their `__init__.py` docstring.

```python
"""
Core authentication and authorization system.

auth/
├── __init__.py        # Package init and public exports.
├── backends/          # Pluggable authentication backends. [1:25]
├── config.py          # Auth configuration and constants.
├── tokens.py          # JWT creation and validation.
│   ├── Token           # Represents a JWT token. [12:45]
│   ├── create_token    # Create a signed JWT. [47:82]
│   └── validate_token  # Verify signature and expiry. [84:120]
└── utils.py           # Shared helper functions.
"""
```

- `backends/ [1:25]` — read `backends/__init__.py` lines 1-25 to get its docstring.
- `tokens.py` has 3 public definitions — gets sub-entries with description + `[start:end]`.
- `config.py` and `utils.py` have fewer than 3 — file-level description only.
- Classes first, then functions, both alphabetical.
- Descriptions come from docstrings (`ast.get_docstring`). Line ranges from `ast.parse()`.
