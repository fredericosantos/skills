---
name: ghx
description: Guide for GitHub project management via `gh` CLI — issues, PRs, milestones, sub-issues, projects, and development workflow. Use this whenever you need to interact with GitHub issues, milestones, sub-issues, PRs, or projects. Also use when planning work, creating branches, structuring issues, or starting a development session on a repository.
allowed-tools:
  - Bash(gh project list)
  - Bash(gh milestone list)
  - Bash(gh issue list *)
  - Bash(gh pr list *)
---

# gh-project

## Extensions required

Milestones and sub-issues have no native `gh` subcommand. Install these extensions:

```bash
gh extension install valeriobelli/gh-milestone   # gh milestone list/create/edit/delete/view
gh extension install agbiotech/gh-sub-issue      # gh sub-issue list/add/remove/reprioritize
```

## First-time setup

Every repository should have its issues tracked in a GitHub Project. Projects are owned by the user/org, not the repo — one Project can span multiple repos. If no Project contains issues from this repo, create and link one:

```bash
gh project list
gh project create --owner OWNER --title "Repo Name"
gh project link NUMBER --repo OWNER/REPO --owner OWNER
```

Then notify the user to configure these **built-in Project workflows** in the browser (Project → Settings → Workflows) — these cannot be set via CLI:

- **Auto-add** — automatically adds new issues/PRs to the Project
- **Item closed** — auto-moves to Done when an issue is closed
- **PR merged** — auto-moves to Done when a PR merges

Set up these Project views:

- **Board** (kanban) — columns: Backlog, In Progress, Review, Done
- **Table** — filterable by milestone, label, assignee
- **Roadmap** — milestones over time

## Session start

This data is fetched automatically when the skill triggers:

- Projects: !`gh project list`
- Milestones: !`gh milestone list`
- Open issues: !`gh issue list --state open --limit 50`
- Open PRs: !`gh pr list --state open`

Review the data above, present a brief summary (what's active, what's blocked, what's next), then ask:

1. **Work on something new** — create a new milestone/issue and start
2. **Work on existing** — pick a milestone, issue, or sub-issue to continue
3. **Organize** — triage unorganized items into the project board

If no Project exists, follow First-time setup first.

### Organize flow

Run `scripts/organize.sh scan` to discover issues not yet in the Project or missing a status.

**If more than 20 unorganized issues**: skip the interactive menu — automatically set all of them to Backlog via `organize.sh apply` and notify the user: "Added N issues to the Project as Backlog. You can reorganize specific items later." This avoids burning tokens on bulk triage.

**If 20 or fewer**: use `AskUserQuestion` to let the user choose:

1. First question: "Organize per milestone, per item, or skip?"
2. If per milestone: one `AskUserQuestion` per milestone with options Backlog / In Progress / Done / Skip
3. If per item: batch into groups (max 4 per question) with the same options
4. Parse answers into a choices JSON: `{"42": "Backlog", "43": "In Progress"}`
5. Run `scripts/organize.sh apply --choices '...'`

## Development workflow

### Work sizing

| Size | Structure | Example |
|---|---|---|
| Big — advances the project in a major way, multiple moving parts | **Milestone** with issues, each issue has sub-issues | "New tree evaluation strategy" |
| Small — single feature, fix, or change | **Issue** with sub-issues if needed | "Fix duplicate fitness values" |

Rule of thumb: if you can't see a 3-layer breakdown (milestone → issues → sub-issues), it's just an issue.

### Labels

Standardized labels — always available:

| Label | Purpose |
|---|---|
| `bug` | Something broken |
| `enhancement` | Improvement to existing feature |
| `performance` | Optimization work |
| `research` | Exploration, no guaranteed outcome |
| `documentation` | Docs, reports, session logs |
| `testing` | Test coverage |
| `needs-revision` | References outdated code, needs update |

Additional labels can be created as needed for project-specific concerns.

### Branch naming

Branches follow `{tag}/{issue-number}-{description}` format. For sub-issues under a milestone, nest: `{tag}/{issue-number}-{description}/{subissue-number}-{subdescription}`.

Tags align with conventional commits and labels:

| Tag | Label | Use |
|---|---|---|
| `feat` | `enhancement` | New feature |
| `fix` | `bug` | Bug fix |
| `refactor` | — | Code restructuring |
| `perf` | `performance` | Optimization |
| `docs` | `documentation` | Documentation |
| `test` | `testing` | Test coverage |
| `research` | `research` | Exploration |

Examples:

```
feat/42-batch-tree-eval                          # standalone issue
feat/42-batch-tree-eval/43-fitness-function      # sub-issue branch
fix/7-duplicate-fitness                          # bug fix
```

### PR targeting

- **Milestone work (cascade):** sub-issue PRs target the parent issue branch, parent issue PR targets main. This keeps review layered and history clean.
- **Standalone issues (flat):** PR targets main directly.

### Commit messages

Follow conventional commits and always reference the issue:

```
feat(eval): implement batch forward pass #42
fix(fitness): deduplicate train fitness output #7
refactor(population): extract layer size computation
perf(crossover): reduce broadcast memory #61
```

### Issue structure

Issues should follow this template:

```markdown
## Summary
What and why.

## Changes Required
What needs to change, in which files.

## Dependencies
Issues that must be resolved first: #X, #Y

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
```

### Dependencies

Issues can list dependencies on other issues. Before closing an issue:

1. Check that all listed dependencies are resolved (their issues are closed)
2. If a dependency is still open, either block the close or document in a comment why the dependency is no longer required

### Delegating issue creation to subagents

When planning work, the primary agent (opus/sonnet) writes the issue content — title, body, labels, milestone, sub-issue relationships, and initial Project status (Backlog or In Progress). Then delegate to a haiku subagent to execute the `gh` commands:

```
Create these issues on GitHub:

1. Issue: "Batch tree evaluation" — label: enhancement, milestone: "New Eval Strategy"
   Body: [full body text]
   Project status: In Progress
   Sub-issues:
     a. "Implement fitness function" — label: enhancement
        Body: [full body text]
        Project status: Backlog
     b. "Update forward pass" — label: enhancement
        Body: [full body text]
        Project status: Backlog

2. Set up sub-issue relationships after creation.
```

The haiku subagent creates issues, sets labels/milestones, adds to Project, creates sub-issue relationships, and sets status. It does not decide what to implement — it only executes what it's told.

The primary agent starts working immediately after delegation, without waiting for the subagent to finish.

### Milestone lifecycle

- Create a milestone when planning big work
- All issues under it should be added to the milestone and the Project
- When the last issue under a milestone is closed, check and close the milestone
- Close stale milestones whose issues reference outdated code — tag remaining issues `needs-revision`

### Stale detection

When the user (or another agent) asks, audit issues for staleness:

- Check if referenced files, functions, or methods still exist in the codebase
- Tag stale issues with `needs-revision`
- Offer to revise or close them

You can also proactively ask the user if they want to audit stale issues when you notice references to deleted code during normal work.

## Command reference

All commands support `--repo owner/repo` or `-R owner/repo` for cross-repo operations.

### Milestones (extension)

```bash
gh milestone list                        # list open milestones
gh milestone list --state closed         # list closed
gh milestone create                      # interactive create
gh milestone edit 3                      # edit milestone #3
gh milestone delete 3                    # delete milestone #3
gh milestone view 3                      # view milestone #3
```

### Sub-issues (extension)

```bash
gh sub-issue list 71                     # list sub-issues of issue #71
gh sub-issue add 71 --sub-issue-number 72          # add #72 as sub-issue of #71
gh sub-issue remove 71 --sub-issue-number 72       # remove sub-issue relationship
gh sub-issue reprioritize 71 --sub-issue-number 74 --before 72  # reorder
```

### Issues (native)

```bash
gh issue list --milestone "v2.0" --state all
gh issue view 13 --json body -q .body
gh issue close 16 --comment "Stale" --reason "not planned"
```

### PRs (native)

```bash
gh pr list --state all
gh pr view 42 --json comments,reviews -q '.comments[].body'
```

### Projects (native)

```bash
gh project list                          # defaults to --owner @me
gh project create --owner OWNER --title "Title"
gh project link 4 --repo OWNER/REPO --owner OWNER
gh project delete 2 --owner OWNER
```
