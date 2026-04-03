---
name: ghp:work
description: See all in-progress issues and pick the best one to continue working on. Checks blocking relationships to find unblocked work.
allowed-tools:
  - Bash(gh issue list *)
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

   Also check Review for items that may need attention:
   ```bash
   gh pm list --status review
   ```

2. **Check blocking status.** For each In Progress and Todo issue, run `gh issue-ext blocking list <number>` to find which are unblocked.

3. **Present to the user** sorted by status and priority (In Progress first, then Todo; milestone work before standalone):

   ```
   In Progress (unblocked):
     #43 Implement fitness function [m7-new-eval-strategy/feat/42-batch-tree-eval/43-fitness-function]
     #7  Fix duplicate fitness values [fix/7-duplicate-fitness]

   Todo (ready to start):
     #45 Add benchmarks [m7-new-eval-strategy/test/45-benchmarks]

   Blocked (waiting on other issues):
     #44 Update forward pass — blocked by #43

   In Review:
     #41 Refactor node types — PR #12 open
   ```

4. **Ask the user** via `AskUserQuestion` which issue to work on (show up to 4 unblocked options).

5. **Check out the linked branch.** Use `gh issue-ext branch list <number>` to find the branch name, then `git checkout <branch>`.

6. **Update status** if starting a Todo item: `gh pm move <number> --status in_progress`.

7. **Create task list.** Check if the issue has sub-issues with `gh issue-ext sub list <number>`. If it does, create a `TaskList` with sub-issues as the first tasks and the parent issue as the final task:
   ```
   TaskCreate: "#43 — Implement fitness function"
   TaskCreate: "#44 — Update forward pass"
   TaskCreate: "#42 — Batch tree evaluation (parent — wrap up when sub-issues done)"
   ```
