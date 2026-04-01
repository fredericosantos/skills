---
name: ghp:init
description: Start a development session on a repository. Reads project state, summarizes what's active/blocked/next, and asks whether to work on something new, continue existing work, or organize issues.
allowed-tools:
  - Bash(git rev-parse *)
  - Bash(git remote *)
  - Bash(gh project list)
  - Bash(gh milestone list)
  - Bash(gh issue list *)
  - Bash(gh pr list *)
---

# /ghp:init — Session Start

## Prerequisites

- Git repo: !`git rev-parse --is-inside-work-tree 2>&1`
- Remote: !`git remote get-url origin 2>&1`

If not a git repo or no remote, stop and notify the user. This workflow requires a GitHub-hosted repository.

## Auto-fetched context

- Projects: !`gh project list`
- Milestones: !`gh milestone list`
- Open issues: !`gh issue list --state open --limit 50`
- Open PRs: !`gh pr list --state open`

## Flow

1. Review the data above. Present a brief summary: what's active, what's blocked, what's next in the backlog.
2. If no Project contains issues from this repo, run the skill's `scripts/organize.sh scan` (which auto-creates and links a Project).
3. Ask the user via `AskUserQuestion`:

| Option | Action |
|---|---|
| Work on something new | Follow the "Delegating issue creation to subagents" section in the main ghp skill: plan the work, write issue content, delegate to haiku to create issues/milestones/blocking/branches, then start coding. For milestones, create a milestone branch first: `git checkout -b m{number}-{short-name}` |
| Work on existing | Run `/ghp:work` to pick an in-progress issue |
| Organize | Run `/ghp:organize` to triage issues into the Project board |
