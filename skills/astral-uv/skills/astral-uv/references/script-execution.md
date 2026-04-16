# Script Execution Examples

## Running a Single Script

```bash
# Run a script with temporary dependencies
uv run --with requests,pandas script.py

# Add dependencies inline to the script
uv add --script data_processor.py pandas numpy
```

## Tool Execution Examples

```bash
# Run linters and formatters
uvx ruff check .
uvx ruff format .

# Run specific versions
uvx pytest@8.0.0
uvx black@23.12.0 .
```