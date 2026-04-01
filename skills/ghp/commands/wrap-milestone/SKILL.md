---
name: ghp:wrap-milestone
description: Close out a milestone. Writes a summary comment, creates a PR from the milestone branch to main, closes all completed issues, and closes the milestone.
allowed-tools:
  - Bash(gh issue *)
  - Bash(gh pr *)
  - Bash(gh milestone *)
  - Bash(gh issue-ext *)
  - Bash(git *)
---

# /ghp:wrap-milestone — Close Out a Milestone

## Flow

1. **Identify the milestone.** If not specified, infer from the current branch name: `m7-new-eval-strategy` → milestone #7. Or ask the user.

2. **Check all issues.** List issues in the milestone with `gh issue list --milestone "Name" --state all`. Verify all are closed or ready to close. If any are still open, show them and ask whether to proceed or stop.

3. **Check blocking relationships.** For any still-open issues, run `gh issue-ext blocking list` to understand why they're open.

4. **Create the PR** from the milestone branch to main. The PR body must include `closes #N` for every completed issue under the milestone:

   ```bash
   gh pr create --base main \
     --title "feat: Milestone Name" \
     --body "## Summary
   <what this milestone achieved>

   ## Issues closed
   closes #42
   closes #43
   closes #44
   closes #45

   ## Milestone
   Closes milestone: Name"
   ```

5. **After PR is merged**, close the milestone:
   ```bash
   gh milestone edit <number> --state closed
   ```

6. **Notify the user** with the PR URL, list of closed issues, and confirmation that the milestone is closed.
