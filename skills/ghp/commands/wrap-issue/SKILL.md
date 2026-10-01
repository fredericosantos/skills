---
name: ghp:wrap-issue
description: Close out an issue. Opens a PR to its parent branch (milestone base, parent issue branch, or main) and merges it once the user agrees. When the PR merges into a branch other than the default one, it closes the issue and its sub-issues itself. Then it removes the worktree and deletes the merged branch, once nothing is using them.
allowed-tools:
  - Bash(gh issue *)
  - Bash(gh pr *)
  - Bash(gh issue-ext *)
  - Bash(gh pm *)
  - Bash(git *)
  - Bash(lsof *)
---

# /ghp:wrap-issue — Close Out an Issue

## Flow

1. **Identify the issue.** If not specified, infer from the current branch name. The branch naming convention encodes the issue number:
   - Milestone issue: `m7/42-batch-tree-eval` → issue #42
   - Sub-issue: `m7/42/43-fitness-function` → issue #43
   - Standalone: `7-duplicate-fitness` → issue #7

2. **Check sub-issues.** Run `gh issue-ext sub list <issue>` to find sub-issues. Verify all are closed or ready to close. If any are still open, ask the user whether to close them or stop.

3. **Check blockers.** Run `gh issue-ext blocking list <issue>` to confirm no unresolved blockers remain.

4. **Determine the target branch** from the current branch name:
   - Sub-issue branch `m7/42/43-...` → PR targets the parent issue branch `m7/42-...`
   - Issue branch `m7/42-...` → PR targets the milestone branch `m7-{name}`
   - Standalone branch → PR targets main

5. **Set issue status to Review** in the Project: `gh pm move <issue> --status review`, with the repo's key for that column ("Board columns and fields" in the main ghp skill). Review means "work complete, PR open".

6. **Create the PR.** The PR body must include `closes #<issue>` and `closes #<sub-issue>` for every completed sub-issue:

   ```bash
   gh pr create --base m7-new-eval-strategy \
     --title "feat(eval): batch tree evaluation #42" \
     --body "## Summary
   <what changed>

   closes #42
   closes #43
   closes #44"
   ```

7. **Write a summary comment** on the issue:
   ```bash
   gh issue comment 42 --body "## Summary
   <brief description of what was done, key changes>

   PR: #N"
   ```

8. **Merge, once the user agrees.** Ask via `AskUserQuestion`. Merge with the repo's `merge_method` from `.ghp.yml` (a merge commit unless it says `squash` or `rebase`). Never pass `--delete-branch`: git refuses to delete a branch that a worktree has checked out, so step 10 deletes it instead.
   ```bash
   gh pr merge <pr> --merge
   ```
   If the user wants to merge later, stop here, and run steps 9–11 after the merge.

9. **Close what the merge didn't.** GitHub acts on `closes #N` only for merges into the default branch. If the PR's base is a milestone base or a parent issue branch, close the issue and every sub-issue the PR lists, and move each to Done:
   ```bash
   gh issue close 42 --comment "Merged into m7-new-eval-strategy via #<pr>. <one-line summary>"
   gh pm move 42 --status done
   ```
   For a PR into the default branch, GitHub closed them. Confirm with `gh issue view 42 --json state`.

10. **Remove the worktree and delete the merged branch.** Run this from the main checkout, never from inside the worktree. First confirm that the PR merged and that the local branch has nothing beyond what merged:
    ```bash
    gh pr view <pr> --json state,headRefOid -q '.state + " " + .headRefOid'   # MERGED <sha>
    git rev-parse m7/42-batch-tree-eval                                        # must print the same <sha>
    ```
    Then check that nothing is using the worktree ("Worktrees" in the main ghp skill):
    ```bash
    git worktree list --porcelain     # a "locked" line under .claude/worktrees/42-batch-tree-eval → stop
    lsof +D .claude/worktrees/42-batch-tree-eval   # any output → stop
    ```
    If something is locked, in use, or has uncommitted files, stop and tell the user what holds it. Never `--force`. Otherwise ask via `AskUserQuestion` (Delete / Keep), then:
    ```bash
    git worktree remove .claude/worktrees/42-batch-tree-eval
    git branch -D m7/42-batch-tree-eval        # safe: its tip is the merged PR head
    git push origin --delete m7/42-batch-tree-eval
    ```
    Do the same for each sub-issue branch that was merged into this branch.

11. **Notify the user** with the PR URL, the issues closed, and what was deleted or kept.
