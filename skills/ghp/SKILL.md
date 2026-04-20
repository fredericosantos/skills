---
name: ghp
description: Guide for GitHub project management via `gh` CLI — issues, PRs, milestones, sub-issues, projects, and development workflow. Use this whenever you need to interact with GitHub issues, milestones, sub-issues, PRs, or projects. Also use when planning work, creating branches, structuring issues, or starting a development session on a repository.
---

# ghp — GitHub Project Management

This skill provides the development workflow reference. Use these commands for specific actions:

- `/ghp:init` — Start a session: read project state, summarize, and pick what to work on
- `/ghp:fresh` — Bootstrap a fresh agent onto an issue (or pick from Todo)
- `/ghp:new-milestone` — Create a milestone with issues, branches, and project tracking in one flow
- `/ghp:work` — See in-progress issues and pick the best one to continue
- `/ghp:wrap-issue` — Close out an issue: summarize, PR to milestone branch, close sub-issues
- `/ghp:wrap-milestone` — Close out a milestone: summarize, PR to main, close issues
- `/ghp:organize` — Triage unorganized issues into the Project board
- `/ghp:cleanup` — Clean up stale branches, dead milestones, and orphaned issues
- `/ghp:create-template` — Scaffold a Project with standard board layout and mark as template

## Extensions required

Milestones, blocking relationships, branches, sub-issues, and project management have no native `gh` subcommand. Install these extensions:

```bash
gh extension install yahsan2/gh-pm              # gh pm list/move/create/intake/triage/split/view
gh extension install valeriobelli/gh-milestone   # gh milestone list/create/edit/delete/view
gh extension install jwilger/gh-issue-ext        # gh issue-ext blocking/sub/branch/show
```

## First-time setup

Every repository should have its issues tracked in a GitHub Project. Initialize the `gh pm` config for the repo:

```bash
gh pm init --project "Repo Name" --repo OWNER/REPO
```

This creates a `.gh-pm.yml` config file so all `gh pm` commands know the project and repo automatically — no `--owner`/`--project` flags needed.

If the Project doesn't exist yet, create and link it first:

```bash
gh project create --owner OWNER --title "Repo Name"
gh project link NUMBER --repo OWNER/REPO --owner OWNER
gh pm init --project "Repo Name" --repo OWNER/REPO
```

Then notify the user to configure these **built-in Project workflows** in the browser (Project → Settings → Workflows) — these cannot be set via CLI:

- **Auto-add** — automatically adds new issues/PRs to the Project
- **Item closed** — auto-moves to Done when an issue is closed
- **PR merged** — auto-moves to Done when a PR merges

Set up these Project views:

- **Board** (kanban) — columns: Backlog, Todo, In Progress, Review, Done
- **Table** — filterable by milestone, label, assignee
- **Roadmap** — milestones over time

Use `/ghp:create-template` to scaffold a project with these columns and mark it as a reusable template.

## Development workflow

### Work sizing

| Size | Structure | Example |
|---|---|---|
| Big — advances the project in a major way, multiple moving parts | **Milestone** with issues, each issue has sub-issues | "Milestone 7 - New Eval Strategy" |
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

**Milestone branches:** `m{N}-{short-name}` — created when planning a milestone.

**Issue branches:** `m{N}/{issue-number}-{short-name}` — uses `m{N}/` prefix (not the full milestone branch name) to avoid git ref conflicts.

**Sub-issue branches:** `m{N}/{issue-number}/{sub-issue-number}-{short-name}`

**Standalone issue branches (no milestone):** `{issue-number}-{short-name}`

**Keep `{short-name}` to 3–4 words max** (e.g. `batch-tree-eval`, not `implement-batch-tree-evaluation-for-forward-pass`). The slug is derived from the issue title via `slugify()`, so write issue titles tersely — long titles produce unwieldy branch names that are painful to type, tab-complete, and read in `git log`.

Always create branches via `gh issue-ext branch create` to link them to the issue on GitHub:

```bash
# Milestone branch (create manually, no issue to link)
git checkout -b m7-new-eval-strategy

# Issue branch under a milestone
gh issue-ext branch create 42 --name m7/42-batch-tree-eval

# Sub-issue branch under an issue
gh issue-ext branch create 43 --name m7/42/43-fitness-function

# Standalone issue branch (no milestone)
gh issue-ext branch create 7 --name 7-duplicate-fitness
```

### Task list on branch creation

When creating a linked branch for an issue that has sub-issues, create a `TaskList` to track progress. Sub-issues become the first tasks, and the parent issue is the final task:

```
# For issue #42 with sub-issues #43, #44, #45:
TaskCreate: "#43 — Implement fitness function"
TaskCreate: "#44 — Update forward pass"
TaskCreate: "#45 — Add benchmarks"
TaskCreate: "#42 — Batch tree evaluation (parent — wrap up when sub-issues done)"
```

Mark each task as `completed` when the corresponding sub-issue is closed. The parent task is completed last via `/ghp:wrap-issue`.

### PR targeting and closing

- **Milestone work (cascade):** sub-issue PRs target the parent issue branch, parent issue PR targets the milestone branch, milestone PR targets main.
- **Standalone issues (flat):** PR targets main directly.

PR bodies must include `closes #N` for every issue/sub-issue being completed:

| PR | Target | Closes |
|---|---|---|
| Sub-issue branch → issue branch | Issue branch | `closes #sub-issue` |
| Issue branch → milestone branch | Milestone branch | `closes #issue` + all completed sub-issues |
| Milestone branch → main | main | All completed issues under the milestone |

Use `/ghp:wrap-issue` and `/ghp:wrap-milestone` to automate this.

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

After creating issues for a milestone, set up blocking relationships using `gh issue-ext`:

```bash
gh issue-ext blocking add 43 42    # #43 is blocked by #42 (do #42 first)
gh issue-ext blocking list 43      # show what blocks #43 and what #43 blocks
gh issue-ext show 42               # show ALL relationships for #42
```

Before closing an issue:

1. Run `gh issue-ext blocking list` to check all dependencies are resolved
2. If a blocker is still open, either block the close or document in a comment why the dependency is no longer required

### Automating issue creation

When planning work, the primary agent writes a YAML plan file describing all issues, sub-issues, labels, blocking relationships, and statuses. Then runs the `create-milestone.py` script to create everything on GitHub in one call.

1. Read the template at `skills/ghp/assets/milestone-template.yml`
2. Fill in the issues with local integer IDs (used only for `blocked_by` references within the YAML)
3. Run: `python skills/ghp/scripts/create-milestone.py plan.yml`

The script creates the milestone, issues, sub-issues, branches, blocking relationships, and project statuses — mapping local IDs to real GitHub issue numbers automatically.

See `/ghp:new-milestone` for the full workflow.

**Status assignment for new issues:**
- The parent issue being worked on now → `In Progress`
- Sub-issues not yet started → `Todo`
- Issues with unresolved blockers → `Backlog`

The haiku subagent creates issues, sets labels/milestones, adds to Project, creates sub-issue and blocking relationships, and sets status. It does not decide what to implement — it only executes what it's told.

The primary agent starts working immediately after delegation, without waiting for the subagent to finish.

### Syncing plans to issues

After creating or updating a plan, delegate to a haiku subagent to post it to the corresponding GitHub issue. The subagent receives only the file path and the issue number — no other context:

```
Read the file at <plan-file-path> and post its contents as a comment on GitHub issue #<number>:

gh issue comment <number> --body "## Plan

<contents of the file>"
```

Derive the issue number from the current branch name:
- `m7-new-eval-strategy/feat/42-batch-tree-eval` → issue #42
- `fix/7-duplicate-fitness` → issue #7

This keeps the issue as the single source of truth for what was planned and what was done.

### Milestone naming

Milestones follow a standardized naming convention:

```
Milestone {number} - {Title}
```

Examples: `Milestone 7 - New Eval Strategy`, `Milestone 12 - Float Constants`

The milestone number matches the GitHub milestone number assigned on creation.

### Milestone lifecycle

- Create a milestone when planning big work: `gh milestone create` with name `Milestone {N} - {Title}`
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

### Project management (extension: gh-pm)

```bash
gh pm init                                   # interactive setup, creates .gh-pm.yml
gh pm list                                   # list all project issues
gh pm list --status in_progress              # filter by status
gh pm list --priority p0,p1                  # filter by priority
gh pm list --assignee @me                    # filter by assignee
gh pm view 42                                # view issue with project metadata
gh pm move 42 --status in_progress           # change status
gh pm move 42 --priority high                # change priority
gh pm create --title "Fix bug" --status todo # create issue and add to project
gh pm intake                                 # list issues not in project
gh pm intake --dry-run                       # preview without adding
gh pm split 123 --from=body                  # split issue body checklist into sub-issues
gh pm split 123 "Task 1" "Task 2"            # split from arguments
gh pm triage name                            # run triage rules from .gh-pm.yml
gh pm triage --query="status:backlog" --apply="status:in_progress"  # ad-hoc triage
```

### Milestones (extension: gh-milestone)

```bash
gh milestone list                        # list open milestones
gh milestone list --state closed         # list closed
gh milestone create                      # interactive create
gh milestone edit 3                      # edit milestone #3
gh milestone delete 3                    # delete milestone #3
gh milestone view 3                      # view milestone #3
```

### Issue relationships (extension: gh-issue-ext)

```bash
# Sub-issues
gh issue-ext sub list 42                     # list sub-issues of #42
gh issue-ext sub add 42 43                   # add #43 as sub-issue of #42
gh issue-ext sub remove 42 43                # remove sub-issue relationship
gh issue-ext sub reorder 42 43 --before 44   # reorder sub-issues

# Blocking
gh issue-ext blocking add 43 42              # #43 is blocked by #42
gh issue-ext blocking remove 43 42           # remove blocking relationship
gh issue-ext blocking list 43                # show blockers and what #43 blocks

# Branches
gh issue-ext branch create 42 --name feat/42-desc  # create linked branch
gh issue-ext branch list 42                  # list linked branches

# All relationships at once
gh issue-ext show 42                         # parent, sub-issues, blocking, branches
```

### Issues (native)

```bash
gh issue list --milestone "Milestone 7 - New Eval Strategy" --state all
gh issue view 13 --json body -q .body
gh issue close 16 --comment "Stale" --reason "not planned"
```

### PRs (native)

```bash
gh pr list --state all
gh pr view 42 --json comments,reviews -q '.comments[].body'
```

### Projects (native — only for initial setup)

```bash
gh project list                          # defaults to --owner @me
gh project create --owner OWNER --title "Title"
gh project link 4 --repo OWNER/REPO --owner OWNER
```
