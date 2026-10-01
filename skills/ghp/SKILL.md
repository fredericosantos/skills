---
name: ghp
description: Guide for GitHub project management via `gh` CLI — issues, PRs, milestones, sub-issues, projects, and development workflow. Use this whenever you need to interact with GitHub issues, milestones, sub-issues, PRs, or projects. Also use when planning work, creating branches, structuring issues, or starting a development session on a repository.
---

# ghp — GitHub Project Management

This skill provides the development workflow reference. Use these commands for specific actions:

- `/ghp:init` — Start a session: read project state, check the repo setup, summarize, and pick what to work on
- `/ghp:fresh` — Bootstrap a fresh agent onto an issue (or pick from Todo)
- `/ghp:new-milestone` — Create a milestone with issues, branches, and project tracking in one flow
- `/ghp:work` — Pick an issue to work on and open its linked branch in its own worktree
- `/ghp:sync` — Merge main into a milestone base and bring the open issue branches along
- `/ghp:adopt` — Bring branches created outside ghp into the ghp structure
- `/ghp:wrap-issue` — Close out an issue: PR to its parent branch, merge, close, remove the worktree
- `/ghp:wrap-milestone` — Close out a milestone: summarize, PR to main, close issues
- `/ghp:organize` — Triage unorganized issues into the Project board
- `/ghp:cleanup` — Clean up stale branches, worktrees, dead milestones, and orphaned issues
- `/ghp:create-template` — Scaffold a Project with standard board layout and mark as template

## Extensions required

Milestones, blocking relationships, sub-issues, and project management have no native `gh` subcommand. Install these extensions:

```bash
gh extension install yahsan2/gh-pm              # gh pm list/move/create/intake/triage/split/view
gh extension install valeriobelli/gh-milestone   # gh milestone list/create/edit/delete/view
gh extension install jwilger/gh-issue-ext        # gh issue-ext blocking/sub/show
```

Linked branches use native `gh issue develop`. The scripts in `${CLAUDE_PLUGIN_ROOT}/scripts/` run with `uv run`, which installs their one dependency (PyYAML).

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

Then run `/ghp:init`. It checks the repo's labels, Status columns and Priority field against this skill and creates what's missing.

Notify the user to configure these **built-in Project workflows** in the browser (Project → Settings → Workflows) — these cannot be set via CLI:

- **Auto-add** — automatically adds new issues/PRs to the Project
- **Item closed** — auto-moves to Done when an issue is closed
- **PR merged** — auto-moves to Done when a PR merges

Set up these Project views:

- **Board** (kanban) — columns: Backlog, Todo, In Progress, Review, Done
- **Table** — filterable by milestone, label, assignee
- **Roadmap** — milestones over time

Use `/ghp:create-template` to scaffold a project with these columns and mark it as a reusable template.

## Repo settings

ghp reads `.ghp.yml` at the repo root. Commit it. It is separate from `.gh-pm.yml` because `gh pm init` rewrites that file from scratch and drops every key gh-pm doesn't know.

```yaml
worktree_setup: uv sync --frozen --group bench   # run in every new worktree
sync_check: uv run pytest -q                     # run after main is merged into a milestone base
merge_method: merge                              # merge, squash or rebase
```

Every key is optional. Without `worktree_setup` or `sync_check`, that step runs nothing and says so. Without `merge_method`, PRs merge with a merge commit. Research repos log commit hashes into experiment trackers, and a squash or rebase merge leaves those hashes on no branch once the issue branch is deleted. Set `merge_method: squash` only in repos that don't record hashes.

## Development workflow

### Work sizing

| Size | Structure | Example |
|---|---|---|
| Big — advances the project in a major way, multiple moving parts | **Milestone** with issues, each issue has sub-issues | "Milestone 7 - New Eval Strategy" |
| Small — single feature, fix, or change | **Issue** with sub-issues if needed | "Fix duplicate fitness values" |

Rule of thumb: if you can't see a 3-layer breakdown (milestone → issues → sub-issues), it's just an issue.

### Labels

Every repo gets one label per role. When the repo already has a label for a role, under the role's name or a synonym, use that label and never create a duplicate:

| Role | Synonyms | Purpose |
|---|---|---|
| `bug` | | Something broken |
| `enhancement` | | Improvement to existing feature |
| `performance` | `perf` | Optimization work |
| `research` | | Exploration, no guaranteed outcome |
| `documentation` | `docs` | Docs, reports, session logs |
| `testing` | `test`, `tests` | Test coverage |
| `needs-revision` | | References outdated code, needs update |

`repo-setup.py` (run by `/ghp:init`) prints which label fills each role and creates only the roles with no label. `create-milestone.py` maps plan labels the same way. Labels in `.gh-pm.yml` `defaults.labels` (such as `pm-tracked`) must exist too, because `gh pm create` applies them verbatim and fails when one is missing.

Additional labels can be created as needed for project-specific concerns.

### Board columns and fields

The standard Status columns, in order: Backlog, Todo, In Progress, Review, Done. An "In Review" option counts as Review.

`gh pm move` and `gh pm create` take a status key from `.gh-pm.yml` `fields.status.values`. Each key is the option name lowercased with spaces turned into `_`, so use the repo's key for a column: `review` on a board whose column is "Review", `in_review` on one whose column is "In Review". A key the file doesn't list makes `gh pm move` fail, and `gh pm create` creates the issue anyway with only a warning.

Priority is a single-select field with the options Critical, High, Medium, Low. Projects v2 fields have no default value, so a new issue gets a Status or Priority only when whatever creates it sets one. `gh pm create` fills both from `.gh-pm.yml` `defaults`. `create-milestone.py` uses `defaults.priority` for plan items without a priority. An issue made with plain `gh issue create` gets neither.

To add a missing Status column without clearing items' values, use `repo-setup.py --apply`. `updateProjectV2Field` replaces the whole option list, and an option sent without its `id` is recreated, which clears it from every item that had it. The script sends every existing option back with its id and checks afterwards that none changed. Never delete and recreate the Status field.

After adding a field or an option, refresh `.gh-pm.yml` so gh-pm can set it: `echo y | gh pm init --project "Repo Name" --repo OWNER/REPO --interactive=false`. Review the diff, because gh-pm rewrites the whole file and resets `defaults.status` to `backlog` (or to `todo` when the board has no Backlog).

### Branch naming

**Milestone branches:** `m{N}-{short-name}` — created when planning a milestone.

**Issue branches:** `m{N}/{issue-number}-{short-name}` — uses `m{N}/` prefix (not the full milestone branch name) to avoid git ref conflicts.

**Sub-issue branches:** `m{N}/{issue-number}/{sub-issue-number}-{short-name}`

**Standalone issue branches (no milestone):** `{issue-number}-{short-name}`

**Keep `{short-name}` to 3–4 words max** (e.g. `batch-tree-eval`, not `implement-batch-tree-evaluation-for-forward-pass`). The slug is derived from the issue title via `slugify()`, so write issue titles tersely — long titles produce unwieldy branch names that are painful to type, tab-complete, and read in `git log`.

### Creating linked branches

Create every issue branch on GitHub with `gh issue develop`, from its parent branch. That links it to its issue and starts it from the right commit:

| Branch | Created from | Command |
|---|---|---|
| Milestone base `m7-new-eval-strategy` | default branch | No issue to link. `create-milestone.py` creates it from the default branch's remote tip. By hand: `git fetch origin main && git push origin origin/main:refs/heads/m7-new-eval-strategy` |
| Issue `m7/42-batch-tree-eval` | milestone base | `gh issue develop 42 --base m7-new-eval-strategy --name m7/42-batch-tree-eval` |
| Sub-issue `m7/42/43-fitness-function` | parent issue branch | `gh issue develop 43 --base m7/42-batch-tree-eval --name m7/42/43-fitness-function` |
| Standalone `7-duplicate-fitness` | default branch | `gh issue develop 7 --base main --name 7-duplicate-fitness` |

The `--base` branch must already exist on the remote. `gh issue develop` fetches the new branch as `origin/<name>` without checking it out, so open it in a worktree (next section). It also records `--base` as the branch's PR base in local git config. List an issue's linked branches with `gh issue develop --list 42`.

Don't use `gh issue-ext branch create`. It always forks from the default branch, whatever the parent is, and it reads `--help` as an issue number. Don't `git checkout -b` an issue branch either: the branch isn't linked to its issue, and it starts from whatever is checked out.

### Worktrees

Work on each issue in its own worktree inside the repo, never in the main checkout and never in a directory beside the repo. One agent per worktree.

- **Path:** `.claude/worktrees/<dir>`, where `<dir>` is the branch name without its `m{N}/` prefix, with `/` turned into `-`. So `m7/42-batch-tree-eval` → `42-batch-tree-eval`, `m7/42/43-fitness-function` → `42-43-fitness-function`, `7-duplicate-fitness` → `7-duplicate-fitness`, and a milestone base keeps its name.
- **Gitignore:** `.claude/` must be gitignored. Add it if it isn't.
- **Create it** after `gh issue develop`, then run the repo's `worktree_setup` in it. Never improvise a setup command: in a repo with opt-in dependency groups, a plain `uv sync` uninstalls them. If `.ghp.yml` has no `worktree_setup`, run nothing and ask the user whether the repo needs one.

  ```bash
  git worktree add --track -b m7/42-batch-tree-eval .claude/worktrees/42-batch-tree-eval origin/m7/42-batch-tree-eval
  # if the local branch already exists:
  git worktree add .claude/worktrees/42-batch-tree-eval m7/42-batch-tree-eval
  ```

- **Lock it (orchestrators):** before handing a worktree to an agent, lock it, and unlock it when the agent reports back. `git worktree remove` refuses a locked worktree even with `--force`.

  ```bash
  git worktree lock --reason "<agent>: <task>" .claude/worktrees/42-batch-tree-eval
  git worktree unlock .claude/worktrees/42-batch-tree-eval
  ```

- **Remove it:** only when nothing is using it. Run these from the main checkout, because a shell inside the worktree shows up as a user.
  1. `git worktree list --porcelain`: a `locked` line under the worktree means an agent holds it. Stop.
  2. `lsof +D .claude/worktrees/42-batch-tree-eval`: any output means a process has its working directory or open files there. Stop. (`fuser` on the directory misses processes working in a subdirectory.)
  3. Even when unlocked and idle, don't remove a worktree that an agent you started might still return to.
  4. `git worktree remove .claude/worktrees/42-batch-tree-eval`. It refuses when there are uncommitted or untracked files. Never `--force`: find out what the files are.

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

### PR targeting, merging and closing

- **Milestone work (cascade):** sub-issue PRs target the parent issue branch, parent issue PR targets the milestone branch, milestone PR targets main.
- **Standalone issues (flat):** PR targets main directly.

PR bodies must include `closes #N` for every issue/sub-issue being completed:

| PR | Target | Closes |
|---|---|---|
| Sub-issue branch → issue branch | Issue branch | `closes #sub-issue` |
| Issue branch → milestone branch | Milestone branch | `closes #issue` + all completed sub-issues |
| Milestone branch → main | main | All completed issues under the milestone |

**GitHub acts on `closes #N` only when the PR merges into the default branch.** A PR merged into a milestone base or a parent issue branch leaves its issues open. `/ghp:wrap-issue` therefore closes them itself after the merge, with a summary comment, and moves them to Done. Keep the `closes` lines anyway, for traceability. The milestone PR into main lists every one.

**Merging:** merge only on the user's go-ahead, with the repo's `merge_method` (`gh pr merge <pr> --merge` unless `.ghp.yml` says otherwise). Never pass `--delete-branch`. It also deletes the local branch, which git refuses while a worktree has that branch checked out. `/ghp:wrap-issue` deletes the branch after removing the worktree.

Use `/ghp:wrap-issue` and `/ghp:wrap-milestone` to automate this.

### Stacked dependencies

When issue B needs issue A's unmerged work, don't build B on A's branch. Land A first:

1. Merge A into the milestone base (`/ghp:wrap-issue` on A).
2. Branch B from the updated base. If B's branch already exists, merge the base into it: `git -C .claude/worktrees/<B> merge origin/m7-new-eval-strategy`.

If B was already built on A's branch and A was then rewritten (rebased, amended, or squash-merged), B still carries A's old commits. Move only B's own commits onto A's new tip, or onto the milestone base if A has landed:

```bash
git fetch origin
old=$(git merge-base --fork-point origin/m7/41-gsgp m7/42-arc)   # the A commit B was built on
git rebase --onto origin/m7/41-gsgp "$old" m7/42-arc            # or --onto origin/m7-new-eval-strategy
git log --oneline origin/m7/41-gsgp..m7/42-arc                   # only B's commits should be listed
git push --force-with-lease origin m7/42-arc
```

`--fork-point` reads A's old tip from the reflog of `origin/m7/41-gsgp`, so it works only if this clone fetched A before the rewrite. If it prints nothing, take the last of A's commits from `git log --oneline m7/42-arc`.

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

When planning a milestone, write a YAML plan describing all issues, sub-issues, labels, blocking relationships, and statuses, then run `create-milestone.py` to create everything on GitHub in one call:

1. Copy `${CLAUDE_PLUGIN_ROOT}/assets/milestone-template.yml` to a scratch location outside the repo and fill it in. The integer IDs are local, used only for `blocked_by` references.
2. Check it: `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/create-milestone.py plan.yml --dry-run`
3. Run the same command without `--dry-run`.

Before creating anything, the script checks every label, status and priority in the plan against the repo and its board. Then it creates, in order: the milestone, the milestone base, the issues (added to the Project), the sub-issue links, the blocking relationships, each linked branch from its parent, and the statuses. It maps local IDs to the GitHub numbers as it goes.

See `/ghp:new-milestone` for the full workflow.

**Status assignment for new issues:**
- The parent issue being worked on now → `In Progress`
- Sub-issues not yet started → `Todo`
- Issues with unresolved blockers → `Backlog`

### Plan record

When the user approves a plan for an issue, post it to the issue as one comment: the plan verbatim, then every decision the user made. Write it to a file and post the file. Never post a summary written from memory:

```markdown
## Plan record

### Plan
<the approved plan, verbatim>

### Decisions
- <question asked> → <the user's answer>
- <option rejected> → <why>
```

```bash
gh issue comment 42 --body-file plan-record.md
```

When the plan changes, post a new `## Plan record` comment. The newest one wins. `/ghp:fresh` builds an agent's brief from the issue body and the newest plan record.

Derive the issue number from the current branch name:
- `m7/42-batch-tree-eval` → issue #42
- `m7/42/43-fitness-function` → issue #43
- `7-duplicate-fitness` → issue #7

This keeps the issue as the single source of truth for what was planned and what was done.

### Milestone naming

Milestones follow a standardized naming convention:

```
Milestone {number} - {Title}
```

Examples: `Milestone 7 - New Eval Strategy`, `Milestone 12 - Float Constants`

The number is the one GitHub assigns on creation, which isn't necessarily the highest number plus one: deleted milestones leave gaps. So create the milestone with its bare title, read its number back from the URL `gh milestone create` prints, then rename it. `create-milestone.py` does this.

### Milestone lifecycle

- Create a milestone when planning big work: `/ghp:new-milestone`
- All issues under it should be added to the milestone and the Project
- When main moves on during the milestone, merge it into the milestone base: `/ghp:sync`
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
gh pm list --priority critical,high          # filter by priority
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

`gh pm create --milestone` is accepted but ignored (gh-pm 0.6.7): for milestone issues, use `gh issue create --milestone` and add the issue to the Project with `gh project item-add`.

### Milestones (extension: gh-milestone)

```bash
gh milestone list                        # list open milestones
gh milestone list --state closed         # list closed
gh milestone create --title "Title"      # prints the new milestone's URL, which ends in its number
gh milestone edit 3 --title "Milestone 3 - Title"
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

# All relationships at once
gh issue-ext show 42                         # parent, sub-issues, blocking, branches
```

### Branches and worktrees (native)

```bash
gh issue develop 42 --base m7-new-eval-strategy --name m7/42-batch-tree-eval   # linked branch from its parent
gh issue develop --list 42                   # linked branches of #42
git worktree list --porcelain                # worktrees, their branches, and lock state
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
gh pr view 42 --json state,headRefOid,baseRefName   # merged? at which commit? into what?
```

### Projects (native)

```bash
gh project list                          # defaults to --owner @me
gh project create --owner OWNER --title "Title"
gh project link 4 --repo OWNER/REPO --owner OWNER
gh project item-add 4 --owner OWNER --url ISSUE_URL   # add an issue made with plain gh issue create
```
