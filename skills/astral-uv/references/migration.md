# Migration Examples

## From pip to uv

```bash
# Old workflow
pip install requests
pip install -r requirements.txt

# New workflow
uv add requests
uv sync
```

## From virtualenv to uv

```bash
# Old workflow
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# New workflow
uv sync
uv run python script.py
```