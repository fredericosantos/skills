# uv Examples

## Project Setup Examples

### Creating a New Project

```bash
# Initialize a new Python project
uv init my-project
cd my-project

# Add dependencies
uv add requests fastapi uvicorn

# Run the project
uv run python -m uvicorn main:app --reload
```

### Adding Development Dependencies

```bash
# Add testing and development tools
uv add --dev pytest black ruff

# Add optional dependencies
uv add --optional pandas
```

## Script Execution Examples

### Running a Single Script

```bash
# Run a script with temporary dependencies
uv run --with requests,pandas script.py

# Add dependencies inline to the script
uv add --script data_processor.py pandas numpy
```

### Tool Execution Examples

```bash
# Run linters and formatters
uvx ruff check .
uvx ruff format .

# Run specific versions
uvx pytest@8.0.0
uvx black@23.12.0 .
```

## Migration Examples

### From pip to uv

```bash
# Old workflow
pip install requests
pip install -r requirements.txt

# New workflow
uv add requests
uv sync
```

### From virtualenv to uv

```bash
# Old workflow
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# New workflow
uv sync
uv run python script.py
```

## Lockfile Management

### Reproducible Environments

```bash
# Install exact versions from lockfile
uv sync

# Update dependencies
uv lock --upgrade

# Check for outdated packages
uv lock --check
```

## Python Version Management

### Managing Python Versions

```bash
# Install specific Python version
uv python install 3.12

# Pin Python version for project
uv python pin 3.12

# Run with specific Python version
uv run --python 3.11 python script.py
```

## Common Workflows

### Web Application Setup

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

### Data Science Project

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

### CLI Tool Development

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