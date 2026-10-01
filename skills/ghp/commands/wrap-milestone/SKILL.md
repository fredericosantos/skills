---
name: ghp:wrap-milestone
description: Close out a milestone. Writes a summary comment, creates a PR from the milestone branch to main, closes all completed issues, and closes the milestone.
allowed-tools:
  - Bash(gh issue *)
  - Bash(gh pr *)
  - Bash(gh milestone *)
  - Bash(gh issue-ext *)
  - Bash(gh pm *)
  - Bash(git *)
  - Bash(lsof *)
---

# /ghp:wrap-milestone — Close Out a Milestone

## Flow

1. **Identify the milestone.** If not specified, infer from the current branch name: `m7-new-eval-strategy` → milestone #7 (`Milestone 7 - ...`). Or ask the user.

2. **Check all issues.** List issues in the milestone with `gh issue list --milestone "Milestone 7 - Name" --state all`. `/ghp:wrap-issue` closes each issue after its PR merges into the milestone base, so all should be closed. If any are still open, show them and ask whether to proceed or stop.

3. **Check blocking relationships.** For any still-open issues, run `gh issue-ext blocking list` to understand why they're open.

4. **Sync with main first** (`/ghp:sync`), so the PR merges cleanly and the repo's `sync_check` has passed on the merged result.

5. **Create the PR** from the milestone branch to main. The PR body must include `closes #N` for every completed issue under the milestone. They are already closed; the list is for traceability, and GitHub closes any that are still open when this PR merges into the default branch:

   ```bash
   gh pr create --base main \
     --title "feat: Milestone 7 - Name" \
     --body "## Summary
   <what this milestone achieved>

   ## Issues closed
   closes #42
   closes #43
   closes #44
   closes #45

   ## Milestone
   Closes milestone: Milestone 7 - Name"
   ```

6. **Merge, once the user agrees**, with the repo's `merge_method` and never `--delete-branch` ("PR targeting, merging and closing" in the main ghp skill). Then close the milestone:
   ```bash
   gh milestone edit <number> --state closed
   ```

7. **Clean up branches and worktrees.** List the milestone base and any remaining issue/sub-issue branches under it (`m{N}/...`), with their worktrees. For each, apply the checks from `/ghp:wrap-issue` step 10: the work is merged, the worktree isn't locked or in use, and there are no uncommitted files. Then ask via `AskUserQuestion` which to delete, and delete worktree, local branch and remote branch in that order.

8. **Notify the user** with the PR URL, list of closed issues, and confirmation that the milestone is closed.
