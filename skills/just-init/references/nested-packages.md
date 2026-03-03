# Nested Packages

Parent package:

```python
"""
Core authentication and authorization system.

auth/
├── __init__.py        # Package init and public exports.
├── config.py          # Auth configuration and constants.
├── tokens.py          # JWT creation, validation, and refresh.
├── backends/          # Pluggable authentication backends.
└── middleware/         # Request authentication middleware.
"""
```

Sub-package (`auth/backends/__init__.py`):

```python
"""
Pluggable authentication backends.

backends/
├── __init__.py        # Package init and backend registry.
├── base.py            # Abstract base class for all backends.
├── ldap.py            # LDAP / Active Directory backend.
└── oauth.py           # OAuth2 / OpenID Connect backend.
"""
```
