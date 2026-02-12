# Project Setup Examples

## Creating a New Project

```bash
# Initialize a new Python project
uv init my-project
cd my-project

# Add dependencies
uv add requests fastapi uvicorn

# Run the project
uv run python -m uvicorn main:app --reload
```

## Adding Development Dependencies

```bash
# Add testing and development tools
uv add --dev pytest black ruff

# Add optional dependencies
uv add --optional pandas
```