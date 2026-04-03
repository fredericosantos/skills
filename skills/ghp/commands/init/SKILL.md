---
name: ghp:init
description: Start a development session on a repository. Reads project state, summarizes what's active/blocked/next, and asks whether to work on something new, continue existing work, or organize issues.
allowed-tools:
  - Bash(git rev-parse *)
  - Bash(git remote *)
  - Bash(gh pm *)
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

- Project config: !`cat .gh-pm.yml 2>/dev/null || echo "No .gh-pm.yml found"`
- Projects for this owner: !`gh project list --owner @me --format json -q '.projects[] | "\(.number) \(.title) template=\(.template)"'`
- Milestones: !`gh milestone list`
- Open issues: !`gh issue list --state open --limit 50`
- Open PRs: !`gh pr list --state open`

## Flow

1. Review the data above. Present a brief summary: what's active, what's blocked, what's next in the backlog.
2. **Project setup check** (only if no `.gh-pm.yml` exists):
   - Check if a GitHub Project already exists for this repo (by name match or linked items).
   - **Project exists** → just run `gh pm init` to create the local config file.
   - **No project exists, but a template exists** → suggest copying from template: `gh project copy <TEMPLATE_NUMBER> --owner @me --title "Repo Name" --drafts`, then link it with `gh project link`, then `gh pm init`.
   - **No project and no template** → suggest: "No project template found. Run `/ghp:create-template` first to create a reusable project template with the standard board layout (Backlog, Todo, In Progress, Review, Done). Then copy from it for this repo."
3. Ask the user via `AskUserQuestion`:

| Option | Action |
|---|---|
| Work on something new | Follow the "Delegating issue creation to subagents" section in the main ghp skill: plan the work, write issue content, delegate to haiku to create issues/milestones/blocking/branches, then start coding. For milestones, create with name `Milestone {N} - {Title}` and branch `m{number}-{short-name}` |
| Work on existing | Run `/ghp:work` to pick an in-progress issue |
| Organize | Run `/ghp:organize` to triage issues into the Project board |
