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
---

# /ghp:wrap-milestone — Close Out a Milestone

## Flow

1. **Identify the milestone.** If not specified, infer from the current branch name: `m7-new-eval-strategy` → milestone #7 (`Milestone 7 - ...`). Or ask the user.

2. **Check all issues.** List issues in the milestone with `gh issue list --milestone "Milestone 7 - Name" --state all`. Verify all are closed or in Review status. If any are still In Progress or earlier, show them and ask whether to proceed or stop.

3. **Check blocking relationships.** For any still-open issues, run `gh issue-ext blocking list` to understand why they're open.

4. **Create the PR** from the milestone branch to main. The PR body must include `closes #N` for every completed issue under the milestone:

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

5. **After PR is merged**, close the milestone:
   ```bash
   gh milestone edit <number> --state closed
   ```

6. **Clean up branches.** Ask the user via `AskUserQuestion` what to do with the milestone branch:

   | Option | Action |
   |---|---|
   | Keep | Leave the branch as-is |
   | Delete local only | `git branch -d <branch>` |
   | Delete remote only | `git push origin --delete <branch>` |
   | Delete both | Delete local and remote |

   Also check for any remaining issue/sub-issue branches under this milestone (`m{N}/...`) and ask about each one separately.

7. **Notify the user** with the PR URL, list of closed issues, and confirmation that the milestone is closed.
