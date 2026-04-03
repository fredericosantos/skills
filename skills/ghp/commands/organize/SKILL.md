---
name: ghp:organize
description: Triage unorganized GitHub issues into a Project board. Scans for issues missing from the Project, presents an interactive menu to set statuses, and applies changes.
allowed-tools:
  - Bash(gh pm *)
  - Bash(gh issue list *)
---

# /ghp:organize — Triage Issues

Run `gh pm intake --dry-run` to discover issues not in the Project.

## If more than 20 unorganized issues

Skip the interactive menu. Add all and set to Backlog:

```bash
gh pm intake
# Then set all to backlog:
gh pm triage --query="-has:status" --apply="status:backlog"
```

Notify the user: "Added N issues to the Project as Backlog. You can reorganize specific items later."

## If 20 or fewer

Use `AskUserQuestion` to let the user choose:

1. First question: "Organize per milestone, per item, or all to Backlog?"
2. If per milestone: one `AskUserQuestion` per milestone with options Backlog / Todo / In Progress / Review / Done / Skip
3. If per item: batch into groups (max 4 per question) with the same options
4. Apply statuses using `gh pm move`:
   ```bash
   gh pm move 42 --status todo
   gh pm move 43 --status in_progress
   ```
