Agent skills for AI coding agents.

## Skills

- **[just-init](skills/just-init/)** - Navigate Python codebases by reading `__init__.py` files before opening other files in a package. Maintain every `__init__.py` as living documentation: a top-level docstring containing a one-line package description, a file tree of `.py` files and subdirectories, and a brief purpose for each entry.
- **[uv](skills/uv/)** - Guide for using uv, the extremely fast Python package and project manager. Use this when working with Python projects, scripts, packages, or tools to manage dependencies, environments, and project setup with universal lockfiles for reproducible builds.
- **[ruff](skills/ruff/)** - Guide for using ruff, the extremely fast Python linter and formatter. Use this when linting, formatting, or fixing Python code to maintain code quality and consistency.
- **[ty](skills/ty/)** - Guide for using ty, the extremely fast Python type checker and language server. Use this when type checking Python code or setting up type checking in Python projects.

## Installing Skills

Use the Skills CLI to install skills from this repository:

```bash
npx skills add fredericosantos/skills@just-init
npx skills add fredericosantos/skills@uv
npx skills add fredericosantos/skills@ruff
npx skills add fredericosantos/skills@ty
```

For more information about the Skills CLI, visit [skills.sh](https://skills.sh).