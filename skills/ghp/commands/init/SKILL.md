---
name: ghp:init
description: Start a development session on a repository. Reads project state, checks the repo's labels, board columns and Priority field against ghp, summarizes what's active/blocked/next, and asks whether to work on something new, continue existing work, or organize issues.
allowed-tools:
  - Bash(git rev-parse *)
  - Bash(git remote *)
  - Bash(gh pm *)
  - Bash(gh milestone list)
  - Bash(gh issue list *)
  - Bash(gh pr list *)
  - Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/repo-setup.py*)
---

# /ghp:init — Session Start

## Prerequisites

- Git repo: !`git rev-parse --is-inside-work-tree 2>&1`
- Remote: !`git remote get-url origin 2>&1`

If not a git repo or no remote, stop and notify the user. This workflow requires a GitHub-hosted repository.

## Auto-fetched context

- Project config: !`cat .gh-pm.yml 2>/dev/null || echo "No .gh-pm.yml found"`
- ghp settings: !`cat .ghp.yml 2>/dev/null || echo "No .ghp.yml found"`
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
3. **Repo setup check.** Report how the repo and its board match ghp:
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/repo-setup.py
   ```
   It prints which label fills each role (for example `documentation -> docs`), each Status column and the option that fills it (`Review -> In Review`), the Priority field, and the command it would run for each gap. It only reads. If something is missing, show the user the list and ask whether to create it:
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/repo-setup.py --apply
   ```
   It creates only the labels with no match, the Priority field (Critical, High, Medium, Low), and the missing Status columns, keeping the existing options' ids so items keep their values ("Board columns and fields" in the main ghp skill). If the user would rather add a column by hand, it's in the board's Status field settings in the browser. Afterwards, run the `gh pm init` refresh the script prints, and show the user the `.gh-pm.yml` diff.
4. **Repo settings check** (only if no `.ghp.yml` exists). Ask the user for `worktree_setup`, `sync_check` and `merge_method` ("Repo settings" in the main ghp skill). Offer only commands that the repo's own docs (CLAUDE.md, README) give for setup and tests, and never guess one. Write the answers to `.ghp.yml` for the user to commit.
5. Ask the user via `AskUserQuestion`:

| Option | Action |
|---|---|
| Work on something new | Big work → `/ghp:new-milestone`. A single issue → write it with the issue template from the main ghp skill, create it with `gh pm create` (the repo's label names, see "Labels"), then `/ghp:work` it |
| Work on existing | Run `/ghp:work` to pick an in-progress issue |
| Organize | Run `/ghp:organize` to triage issues into the Project board |
