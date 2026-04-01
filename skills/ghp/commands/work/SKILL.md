---
name: ghp:work
description: See all in-progress issues and pick the best one to continue working on. Checks blocking relationships to find unblocked work.
allowed-tools:
  - Bash(gh issue list *)
  - Bash(gh issue-ext *)
  - Bash(gh project item-list *)
  - Bash(gh project field-list *)
  - Bash(git *)
---

# /ghp:work — Pick Next Work

## Flow

1. **Find in-progress issues.** Use `gh project item-list` to get items with "In Progress" status:
   ```bash
   gh project item-list <PROJECT> --owner <OWNER> --format json \
     -q '[.items[] | select(.status == "In Progress") | {number: .content.number, title: .content.title}]'
   ```

2. **Check blocking status.** For each in-progress issue, run `gh issue-ext blocking list <number>` to find which are unblocked.

3. **Present to the user** sorted by priority (milestone work first, then standalone):

   ```
   Unblocked and ready:
     #43 Implement fitness function [m7-new-eval-strategy/feat/42-batch-tree-eval/43-fitness-function]
     #7  Fix duplicate fitness values [fix/7-duplicate-fitness]

   Blocked (waiting on other issues):
     #44 Update forward pass — blocked by #43
   ```

4. **Ask the user** via `AskUserQuestion` which issue to work on (show up to 4 unblocked options).

5. **Check out the linked branch.** Use `gh issue-ext branch list <number>` to find the branch name, then `git checkout <branch>`.
