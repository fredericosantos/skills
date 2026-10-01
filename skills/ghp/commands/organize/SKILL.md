---
name: ghp:organize
description: Triage unorganized GitHub issues into a Project board. Scans for issues missing from the Project, presents an interactive menu to set statuses, and applies changes using the repo's own label names and Status columns.
allowed-tools:
  - Bash(gh pm *)
  - Bash(gh issue list *)
  - Bash(gh issue edit *)
  - Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/repo-setup.py*)
---

# /ghp:organize — Triage Issues

1. Run `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/repo-setup.py` (it only reads) to learn the repo's label for each role (`documentation -> docs`) and its Status columns. Apply labels and statuses under those names only. If a label or column is missing, offer `--apply` as `/ghp:init` step 3 does. Never create a label for a role the repo already fills under a synonym.
2. Run `gh pm intake --dry-run` to discover issues not in the Project.

## If more than 20 unorganized issues

Skip the interactive menu. Add all and set them to the board's first column: Backlog, or Todo on a board without a Backlog column (use its `.gh-pm.yml` key):

```bash
gh pm intake
# Then set all to the first column:
gh pm triage --query="-has:status" --apply="status:backlog"
```

Notify the user: "Added N issues to the Project as Backlog (or Todo). You can reorganize specific items later."

## If 20 or fewer

Use `AskUserQuestion` to let the user choose:

1. First question: "Organize per milestone, per item, or all to Backlog?"
2. If per milestone: one `AskUserQuestion` per milestone with the board's columns (Backlog / Todo / In Progress / Review / Done, as the board names them) and Skip
3. If per item: batch into groups (max 4 per question) with the same options
4. Apply statuses using `gh pm move`, and labels with `gh issue edit <n> --add-label <the repo's label>`:
   ```bash
   gh pm move 42 --status todo
   gh pm move 43 --status in_progress
   ```
