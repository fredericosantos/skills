# fredericosantos/skills

Agent skills for AI coding agents.

## Skills

This repository contains skills that teach AI agents specialized workflows and domain knowledge.

### Available Skills

- **[just-init](skills/just-init/)** - Navigate Python codebases by reading `__init__.py` files before opening other files in a package. Maintain every `__init__.py` as living documentation: a top-level docstring containing a one-line package description, a file tree of `.py` files and subdirectories, and a brief purpose for each entry.

## Installing Skills

Use the Skills CLI to install skills from this repository:

```bash
npx skills add fredericosantos/skills@just-init
```

For more information about the Skills CLI, visit [skills.sh](https://skills.sh).

## Contributing

Skills are organized in the `skills/` directory. Each skill is a subdirectory containing at least a `SKILL.md` file with YAML frontmatter and markdown instructions.

To add a new skill:

1. Create a new directory under `skills/` (e.g., `skills/my-skill/`)
2. Add a `SKILL.md` file with proper frontmatter and instructions
3. Test the skill locally
4. Submit a pull request

See [anthropics/skills](https://github.com/anthropics/skills) for examples and best practices.