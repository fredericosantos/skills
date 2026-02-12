# Common Workflows

## Web Application Setup

```bash
# Initialize project
uv init webapp

# Add web framework and dependencies
uv add fastapi uvicorn sqlalchemy

# Add development tools
uv add --dev pytest httpx

# Run development server
uv run uvicorn app:app --reload
```

## Data Science Project

```bash
# Initialize project
uv init data-project

# Add data science stack
uv add pandas numpy matplotlib seaborn scikit-learn jupyter

# Add development tools
uv add --dev pytest black ruff

# Start Jupyter
uv run jupyter notebook
```

## CLI Tool Development

```bash
# Initialize project
uv init cli-tool

# Add CLI framework and dependencies
uv add typer rich

# Add development tools
uv add --dev pytest typer-cli

# Run the tool
uv run python -m cli_tool
```