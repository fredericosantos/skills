# Lockfile Management

## Reproducible Environments

```bash
# Install exact versions from lockfile
uv sync

# Update dependencies
uv lock --upgrade

# Check for outdated packages
uv lock --check
```