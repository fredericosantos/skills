# Automation

The `scripts/just-init.py` script automates docstring management:

```bash
uv run scripts/just-init.py <mode> <path>
```

| Mode | Behavior | Creates files? | Exit code |
|------|----------|----------------|-----------|
| `generate` | Walk all packages, create/update all docstrings | Yes | 0 |
| `verify` | Compare docstrings against directory contents | No | 0=clean, 1=stale |
| `update` | Regenerate only stale docstrings | No | 0 |

- **Descriptions** (`# comment`) are preserved on update. New entries get `# TODO: describe.`
- **Line indexes** and **file trees** are fully automated.

## Claude Code Hook

To auto-verify after Python file changes, add to `.claude/settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "command": "uv run /path/to/skills/just-init/scripts/just-init.py verify .",
        "onFailure": "notify"
      }
    ]
  }
}
```
