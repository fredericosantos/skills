# Update: Adding a Sub-package

Before:

```python
"""
HTTP client wrappers.

client/
├── __init__.py        # Package init and default client factory.
├── async.py           # Asynchronous HTTP client.
└── sync.py            # Synchronous HTTP client.
"""
```

After creating `client/adapters/`. Update the parent:

```python
"""
HTTP client wrappers.

client/
├── __init__.py        # Package init and default client factory.
├── async.py           # Asynchronous HTTP client.
├── sync.py            # Synchronous HTTP client.
└── adapters/          # Transport adapters for different protocols.
"""
```

New `client/adapters/__init__.py`:

```python
"""
Transport adapters for different protocols.

adapters/
├── __init__.py        # Package init and adapter registry.
├── http1.py           # HTTP/1.1 transport adapter.
└── http2.py           # HTTP/2 transport adapter.
"""
```
