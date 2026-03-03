# Update: Adding a File

Before — three files:

```python
"""
HTTP client wrappers.

client/
├── __init__.py        # Package init and default client factory.
├── async.py           # Asynchronous HTTP client.
└── sync.py            # Synchronous HTTP client.
"""
```

After adding `retry.py`:

```python
"""
HTTP client wrappers.

client/
├── __init__.py        # Package init and default client factory.
├── async.py           # Asynchronous HTTP client.
├── retry.py           # Retry policies and backoff strategies.
└── sync.py            # Synchronous HTTP client.
"""
```
