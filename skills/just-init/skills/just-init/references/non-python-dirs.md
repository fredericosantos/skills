# Non-Python Directories

Non-Python directories are listed but not expanded. No `__init__.py` inside them.

```python
"""
Data pipeline for ingesting and transforming CSV feeds.

pipeline/
├── __init__.py        # Package init and pipeline orchestration.
├── fixtures/          # Test fixture data (CSV samples).
├── ingest.py          # Read and validate raw CSV files.
├── load.py            # Write transformed data to the database.
└── transform.py       # Apply cleaning and normalization rules.
"""
```
