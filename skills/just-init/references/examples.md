# Examples

Concrete `__init__.py` docstring patterns for common scenarios.

## Simple Flat Package

```python
"""
Utilities for validating and sanitizing user input.

validation/
├── __init__.py        # Package init and public exports.
├── sanitizer.py       # Strip and escape untrusted strings.
├── email.py           # Validate email address formats.
└── phone.py           # Validate and normalize phone numbers.
"""
```

## Nested Package with Sub-packages

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

Each sub-package gets its own `__init__.py`:

```python
"""
Pluggable authentication backends.

backends/
├── __init__.py        # Package init and backend registry.
├── base.py            # Abstract base class for all backends.
├── oauth.py           # OAuth2 / OpenID Connect backend.
└── ldap.py            # LDAP / Active Directory backend.
"""
```

## Package with Non-Python Directories

Non-Python directories are listed but their contents are not expanded.
Only `.py` files and subdirectory names appear in the tree.

```python
"""
Data pipeline for ingesting and transforming CSV feeds.

pipeline/
├── __init__.py        # Package init and pipeline orchestration.
├── ingest.py          # Read and validate raw CSV files.
├── transform.py       # Apply cleaning and normalization rules.
├── load.py            # Write transformed data to the database.
└── fixtures/          # Test fixture data (CSV samples).
"""
```

## Update Scenario: Adding a New File

Before — the package has three files:

```python
"""
HTTP client wrappers.

client/
├── __init__.py        # Package init and default client factory.
├── sync.py            # Synchronous HTTP client.
└── async.py           # Asynchronous HTTP client.
"""
```

A new file `retry.py` is added. After the edit, update the docstring:

```python
"""
HTTP client wrappers.

client/
├── __init__.py        # Package init and default client factory.
├── sync.py            # Synchronous HTTP client.
├── async.py           # Asynchronous HTTP client.
└── retry.py           # Retry policies and backoff strategies.
"""
```

## Update Scenario: Adding a Sub-package

Before:

```python
"""
HTTP client wrappers.

client/
├── __init__.py        # Package init and default client factory.
├── sync.py            # Synchronous HTTP client.
└── async.py           # Asynchronous HTTP client.
"""
```

A new `client/adapters/` sub-package is created. Update the parent:

```python
"""
HTTP client wrappers.

client/
├── __init__.py        # Package init and default client factory.
├── sync.py            # Synchronous HTTP client.
├── async.py           # Asynchronous HTTP client.
└── adapters/          # Transport adapters for different protocols.
"""
```

And create the new `client/adapters/__init__.py`:

```python
"""
Transport adapters for different protocols.

adapters/
├── __init__.py        # Package init and adapter registry.
├── http1.py           # HTTP/1.1 transport adapter.
└── http2.py           # HTTP/2 transport adapter.
"""
```
