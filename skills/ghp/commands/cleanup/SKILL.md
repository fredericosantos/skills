---
name: ghp:cleanup
description: Clean up stale branches, closed issue remnants, and dead milestones. Scans for branches with no open issue, closed milestones with lingering branches, and issues referencing deleted code. Always asks before deleting.
allowed-tools:
  - Bash(gh issue *)
  - Bash(gh milestone *)
  - Bash(gh issue-ext *)
  - Bash(gh pm *)
  - Bash(git *)
---

# /ghp:cleanup — Clean Up Stale Artifacts

Scans for stale branches, dead milestones, and orphaned issues. Always asks the user before taking action.

## Flow

1. **Scan remote branches:**
   ```bash
   git fetch --prune
   git branch -r --list 'origin/m*'
   ```

   For each remote branch, check if the linked issue is still open. Categorize:
   - **Stale**: issue is closed but branch still exists
   - **Orphaned**: no issue found for this branch
   - **Active**: issue is open

2. **Scan local branches:**
   ```bash
   git branch --list 'm*'
   ```

   Check for local branches whose remote tracking branch is gone (`[gone]`).

3. **Scan milestones:**
   ```bash
   gh milestone list --state open
   ```

   For each open milestone, check if all issues are closed. Flag milestones that should be closed.

4. **Scan for stale issues** (optional — ask the user first since this is slower):
   - Check open issues for references to files, functions, or classes that no longer exist in the codebase
   - Tag stale issues with `needs-revision`

5. **Present findings** to the user, grouped by category:

   ```
   Stale branches (issue closed, branch exists):
     m5/34-improve-init-flow — #34 closed
     m3/12-old-feature — #12 closed

   Local-only branches (remote deleted):
     m4-script-test [gone]

   Milestones ready to close (all issues done):
     Milestone 3 - GHP Improvements (3/3 closed)

   Stale issues (references deleted code):
     #9 — references `scripts/organize.sh` (deleted)
   ```

6. **Ask the user** via `AskUserQuestion` for each category what to do:

   | Category | Options |
   |---|---|
   | Stale branches | Delete both / Delete remote only / Delete local only / Keep |
   | Local-only branches | Delete / Keep |
   | Milestones | Close / Keep open |
   | Stale issues | Tag `needs-revision` / Close / Keep |

7. **Execute** the user's choices and report what was done.
