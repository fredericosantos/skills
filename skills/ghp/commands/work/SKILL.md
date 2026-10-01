---
name: ghp:work
description: See all in-progress issues and pick the best one to continue working on. Checks blocking relationships to find unblocked work, then opens the issue's linked branch in its own worktree and runs the repo's setup command.
allowed-tools:
  - Bash(gh issue list *)
  - Bash(gh issue develop *)
  - Bash(gh issue-ext *)
  - Bash(gh pm *)
  - Bash(git *)
---

# /ghp:work — Pick Next Work

## Flow

1. **Get actionable issues.** Fetch Todo and In Progress items:
   ```bash
   gh pm list --status in_progress
   gh pm list --status todo
   ```

   Also check Review for items that may need attention, using the repo's key for that column (`review` or `in_review`, see "Board columns and fields" in the main ghp skill):
   ```bash
   gh pm list --status review
   ```

2. **Check blocking status.** For each In Progress and Todo issue, run `gh issue-ext blocking list <number>` to find which are unblocked. If an issue's only blocker is finished but not merged, see "Stacked dependencies" in the main ghp skill. Don't build on the blocker's branch.

3. **Present to the user** sorted by status and priority (In Progress first, then Todo; milestone work before standalone):

   ```
   In Progress (unblocked):
     #43 Implement fitness function [m7/42/43-fitness-function]
     #7  Fix duplicate fitness values [7-duplicate-fitness]

   Todo (ready to start):
     #45 Add benchmarks [m7/45-benchmarks]

   Blocked (waiting on other issues):
     #44 Update forward pass — blocked by #43

   In Review:
     #41 Refactor node types — PR #12 open
   ```

4. **Ask the user** via `AskUserQuestion` which issue to work on (show up to 4 unblocked options).

5. **Find or create the linked branch.** `gh issue develop --list <number>` shows it. If there is none, create it from its parent branch ("Creating linked branches" in the main ghp skill):
   ```bash
   gh issue develop 45 --base m7-new-eval-strategy --name m7/45-benchmarks
   ```

6. **Open its worktree.** If `git worktree list` already shows one for the branch, reuse it. Otherwise add one at `.claude/worktrees/<dir>` ("Worktrees" in the main ghp skill gives the naming):
   ```bash
   git fetch origin m7/45-benchmarks
   git worktree add --track -b m7/45-benchmarks .claude/worktrees/45-benchmarks origin/m7/45-benchmarks
   ```
   If the local branch already exists, use `git worktree add .claude/worktrees/45-benchmarks m7/45-benchmarks` instead. If the parent branch has moved on since, merge it in: `git -C .claude/worktrees/45-benchmarks merge origin/m7-new-eval-strategy`.

7. **Run the repo's setup command** in a new worktree: `worktree_setup` from `.ghp.yml`. If there is none, run nothing, and ask the user whether the repo needs one. For example, with `worktree_setup: uv sync --frozen --group bench`:
   ```bash
   cd .claude/worktrees/45-benchmarks && uv sync --frozen --group bench
   ```

8. **Update status** if starting a Todo item: `gh pm move <number> --status in_progress`.

9. **Create task list.** Check if the issue has sub-issues with `gh issue-ext sub list <number>`. If it does, create a `TaskList` with sub-issues as the first tasks and the parent issue as the final task:
   ```
   TaskCreate: "#43 — Implement fitness function"
   TaskCreate: "#44 — Update forward pass"
   TaskCreate: "#42 — Batch tree evaluation (parent — wrap up when sub-issues done)"
   ```

10. **Work only in the worktree.** Run every command there, with absolute paths or `git -C`, and leave the main checkout alone. When the user approves an implementation plan, post it as a plan record ("Plan record" in the main ghp skill) before coding.
