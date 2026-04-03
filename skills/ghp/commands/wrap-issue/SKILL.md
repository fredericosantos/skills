---
name: ghp:wrap-issue
description: Close out an issue. Writes a summary comment, creates a PR to the milestone branch (or main for standalone issues), and closes all completed sub-issues.
allowed-tools:
  - Bash(gh issue *)
  - Bash(gh pr *)
  - Bash(gh issue-ext *)
  - Bash(gh pm *)
  - Bash(git *)
---

# /ghp:wrap-issue — Close Out an Issue

## Flow

1. **Identify the issue.** If not specified, infer from the current branch name. The branch naming convention encodes the issue number:
   - Milestone issue: `m7-new-eval-strategy/feat/42-batch-tree-eval` → issue #42
   - Standalone: `fix/7-duplicate-fitness` → issue #7

2. **Check sub-issues.** Run `gh issue-ext sub list <issue>` to find sub-issues. Verify all are closed or ready to close. If any are still open, ask the user whether to close them or stop.

3. **Check blockers.** Run `gh issue-ext blocking list <issue>` to confirm no unresolved blockers remain.

4. **Determine the target branch** from the current branch name:
   - If branch starts with `m{number}-` → extract the milestone branch prefix (e.g. `m7-new-eval-strategy`) and PR targets that
   - If no milestone prefix → PR targets main

5. **Set issue status to Review** in the Project using `gh pm move <issue> --status review` (signals "work complete, PR open for review"). The built-in "Item closed" workflow auto-moves to Done when the PR merges and closes the issue.

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

8. **Notify the user** with the PR URL and a summary of what was closed.
