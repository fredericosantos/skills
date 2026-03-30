---
name: ghx:init
description: Start a development session on a repository. Reads project state, summarizes what's active/blocked/next, and asks whether to work on something new, continue existing work, or organize issues.
allowed-tools:
  - Bash(gh project list)
  - Bash(gh milestone list)
  - Bash(gh issue list *)
  - Bash(gh pr list *)
---

# /ghx:init — Session Start

## Auto-fetched context

- Projects: !`gh project list`
- Milestones: !`gh milestone list`
- Open issues: !`gh issue list --state open --limit 50`
- Open PRs: !`gh pr list --state open`

## Flow

1. Review the data above. Present a brief summary: what's active, what's blocked, what's next in backlog.
2. If no Project contains issues from this repo, run `scripts/organize.sh scan` (which auto-creates and links a Project).
3. Ask the user via `AskUserQuestion`:

| Option | Action |
|---|---|
| Work on something new | Create a new milestone/issue and start |
| Work on existing | Pick a milestone, issue, or sub-issue to continue |
| Organize | Run `/ghx:organize` flow |
