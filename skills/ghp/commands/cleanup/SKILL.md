---
name: ghp:cleanup
description: Clean up stale branches, worktrees, closed issue remnants, and dead milestones. Scans for merged issue branches, worktrees whose work has merged, branches with no open issue, closed milestones with lingering branches, and issues referencing deleted code. Always asks before deleting.
allowed-tools:
  - Bash(gh issue *)
  - Bash(gh pr *)
  - Bash(gh milestone *)
  - Bash(gh issue-ext *)
  - Bash(gh pm *)
  - Bash(git *)
  - Bash(lsof *)
---

# /ghp:cleanup — Clean Up Stale Artifacts

Scans for stale branches, worktrees, dead milestones, and orphaned issues. Always asks the user before taking action. Run it from the main checkout.

## Flow

1. **Scan remote branches** (milestone `m*` and standalone `<number>-*` branches):
   ```bash
   git fetch --prune
   git branch -r --list 'origin/m*' 'origin/[0-9]*'
   ```

   For each remote branch, check if the linked issue is still open. Categorize:
   - **Stale**: issue is closed but branch still exists
   - **Orphaned**: no issue found for this branch
   - **Active**: issue is open

2. **Scan local branches:**
   ```bash
   git branch --list 'm*' '[0-9]*' -vv
   ```

   Flag local branches whose remote tracking branch is gone (`[gone]`), and merged issue branches: those whose PR is merged and whose tip is the PR head, so nothing would be lost.
   ```bash
   gh pr list --head m5/34-improve-init-flow --state merged --json number,headRefOid
   ```

3. **Scan worktrees:**
   ```bash
   git worktree list --porcelain
   git worktree prune --dry-run      # entries whose directory no longer exists
   ```

   For each worktree under `.claude/worktrees/`, note its branch, whether that branch's PR merged or its issue closed, and whether the worktree can be removed safely. It can't if it's locked (`locked` line), in use (`lsof +D <path>` prints anything), or has uncommitted files (`git -C <path> status --porcelain` prints anything). Those are reported but never offered for deletion.

4. **Scan milestones:**
   ```bash
   gh milestone list --state open
   ```

   For each open milestone, check if all issues are closed. Flag milestones that should be closed.

5. **Scan for stale issues** (optional — ask the user first since this is slower):
   - Check open issues for references to files, functions, or classes that no longer exist in the codebase
   - Tag stale issues with `needs-revision`

6. **Present findings** to the user, grouped by category:

   ```
   Stale branches (issue closed, branch exists):
     m5/34-improve-init-flow — #34 closed
     m3/12-old-feature — #12 closed

   Merged issue branches (PR merged, nothing unmerged):
     m5/35-stale-detection — PR #40 merged

   Local-only branches (remote deleted):
     m4-script-test [gone]

   Worktrees of merged or closed work:
     .claude/worktrees/35-stale-detection — PR #40 merged, idle, clean
     .claude/worktrees/36-cache — #36 closed, LOCKED (agent arc-slim: benchmark), not removable

   Milestones ready to close (all issues done):
     Milestone 3 - GHP Improvements (3/3 closed)

   Stale issues (references deleted code):
     #9 — references `scripts/organize.sh` (deleted)
   ```

7. **Ask the user** via `AskUserQuestion` for each category what to do:

   | Category | Options |
   |---|---|
   | Stale branches | Delete both / Delete remote only / Delete local only / Keep |
   | Merged issue branches | Delete both / Keep |
   | Local-only branches | Delete / Keep |
   | Worktrees | Remove / Keep (only idle, unlocked, clean ones are offered) |
   | Milestones | Close / Keep open |
   | Stale issues | Tag `needs-revision` / Close / Keep |

8. **Execute** the user's choices and report what was done. Remove a worktree before deleting its branch (`git worktree remove <path>`, never `--force`), and re-run the in-use checks right before removing it.
