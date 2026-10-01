---
name: ghp:sync
description: Sync a milestone base with main. Merges the default branch into the milestone base in its own worktree, runs the repo's sync check, pushes, and lists the open issue branches that need to merge the updated base. Use when main has moved on during a milestone, and before /ghp:wrap-milestone.
allowed-tools:
  - Bash(gh issue *)
  - Bash(gh pr *)
  - Bash(git *)
  - Bash(lsof *)
---

# /ghp:sync — Sync a Milestone Base with Main

## Flow

1. **Identify the milestone base** from the current branch (`m7/42-...` → `m7-...`, using `git branch -r --list 'origin/m7-*'`) or ask the user.

2. **Check how far behind it is:**
   ```bash
   git fetch origin
   git rev-list --count origin/m7-new-eval-strategy..origin/main   # 0 → nothing to do, stop
   ```

3. **Merge main into the base in its own worktree**, never in the main checkout. Merge rather than rebase, because the issue branches are built on the base's commits:
   ```bash
   git worktree add .claude/worktrees/m7-new-eval-strategy m7-new-eval-strategy
   # no local branch yet:
   git worktree add --track -b m7-new-eval-strategy .claude/worktrees/m7-new-eval-strategy origin/m7-new-eval-strategy
   git -C .claude/worktrees/m7-new-eval-strategy merge origin/main
   ```
   On conflicts, stop and show the user the conflict diffs before resolving anything. Never resolve with `--ours` or `--theirs` before the user has seen them.

4. **Run the setup and the sync check** in that worktree: `worktree_setup`, then `sync_check`, both from `.ghp.yml`. If there is no `sync_check`, say so. If the check fails, don't push: report the failure and leave the merge in the worktree for the user.

5. **Push the base:**
   ```bash
   git -C .claude/worktrees/m7-new-eval-strategy push origin m7-new-eval-strategy
   ```

6. **List the open issue branches that need the update.** For each `m7/*` branch whose issue is open:
   ```bash
   git rev-list --count origin/m7/42-batch-tree-eval..origin/m7-new-eval-strategy   # commits it lacks
   ```
   Report each branch, how far behind it is, and whether it has a worktree. Don't merge into a worktree another agent may be using. Tell its owner, or the user, to run `git -C .claude/worktrees/<dir> merge origin/m7-new-eval-strategy`. `/ghp:work` also merges the base when it next opens the branch.

7. **Remove the base's worktree** once it's pushed, with the checks from "Worktrees" in the main ghp skill.
