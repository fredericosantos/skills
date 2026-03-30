---
name: ghp:organize
description: Triage unorganized GitHub issues into a Project board. Scans for issues missing from the Project, presents an interactive menu to set statuses, and applies changes.
allowed-tools:
  - Bash(gh project *)
  - Bash(gh issue list *)
  - Bash(bash *organize.sh*)
---

# /ghp:organize — Triage Issues

Run `scripts/organize.sh scan` to discover issues not in the Project or missing a status.

## If more than 20 unorganized issues

Skip the interactive menu. Auto-set all to Backlog:

```bash
# Build choices JSON with all issues set to "Todo"
bash scripts/organize.sh apply --choices '{"42":"Todo","43":"Todo",...}'
```

Notify the user: "Added N issues to the Project as Backlog. You can reorganize specific items later."

## If 20 or fewer

Use `AskUserQuestion` to let the user choose:

1. First question: "Organize per milestone, per item, or all to Backlog?"
2. If per milestone: one `AskUserQuestion` per milestone with options Todo / In Progress / Done / Skip
3. If per item: batch into groups (max 4 per question) with the same options
4. Parse answers into a choices JSON: `{"42": "Todo", "43": "In Progress"}`
5. Run `bash scripts/organize.sh apply --choices '...'`
