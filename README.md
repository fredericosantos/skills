Agent skills for AI coding agents.

## Skills

- **[just-init](skills/just-init/)** - Navigate Python codebases by reading `__init__.py` files before opening other files in a package. Maintain every `__init__.py` as living documentation: a top-level docstring containing a one-line package description, a file tree of `.py` files and subdirectories, and a brief purpose for each entry.
- **[astral-uv](skills/astral-uv/)** - Guide for using uv, the extremely fast Python package and project manager. Use this when working with Python projects, scripts, packages, or tools to manage dependencies, environments, and project setup with universal lockfiles for reproducible builds.
- **[astral-ruff](skills/astral-ruff/)** - Guide for using ruff, the extremely fast Python linter and formatter. Use this when linting, formatting, or fixing Python code to maintain code quality and consistency.
- **[astral-ty](skills/astral-ty/)** - Guide for using ty, the extremely fast Python type checker and language server. Use this when type checking Python code or setting up type checking in Python projects.
- **[dotstate](skills/dotstate/)** - Guide for using dotstate, a profile-based dotfile manager with GitHub sync. Use this when managing dotfiles across multiple machines, adding files to sync, switching profiles, or troubleshooting symlinks.

## Installing Skills

Use the Skills CLI to install skills from this repository:

```bash
npx skills add fredericosantos/skills@just-init
npx skills add fredericosantos/skills@astral-uv
npx skills add fredericosantos/skills@astral-ruff
npx skills add fredericosantos/skills@astral-ty
npx skills add fredericosantos/skills@dotstate
```

For more information about the Skills CLI, visit [skills.sh](https://skills.sh).