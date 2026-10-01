---
name: ghp:adopt
description: Bring existing branches into the ghp structure. Creates or finds each branch's issue, creates a linked branch with the ghp name at the same commit, moves the local branch and its worktree onto it, and deletes the old remote name. Use for work started outside ghp.
allowed-tools:
  - Bash(gh issue *)
  - Bash(gh issue-ext *)
  - Bash(gh pr *)
  - Bash(gh pm *)
  - Bash(gh project *)
  - Bash(git *)
  - Bash(lsof *)
---

# /ghp:adopt — Adopt Existing Branches

GitHub can't link an existing branch to an issue: `gh issue develop` always creates a new branch. So adopt a branch by creating its linked branch at the same commit, under the ghp name, and moving the local branch onto it.

## Flow

1. **Inventory.** For each branch to adopt, settle with the user: its issue (an existing number, or a new one), its parent (milestone base, parent issue branch, or the default branch), and so its ghp name ("Branch naming" in the main ghp skill). Example: `gsgp-arc` → issue #1208 under Milestone 32 → `m32/1208-arc-gsgp`.

2. **Create the missing issues** with the issue template, the repo's label names, and `--milestone` when they belong to one. Add each to the Project and set its status:
   ```bash
   gh issue create --title "ARC on GSGP" --label enhancement --milestone "Milestone 32 - Semantic GP" --body-file issue.md
   gh project item-add <project> --owner <owner> --url <issue-url>
   gh pm move 1208 --status in_progress
   ```

3. **Push the existing branch** so GitHub has its commits: `git push origin gsgp-arc`.

4. **Create the linked branch at the same commit.** With the existing branch as `--base`, the new branch starts at its tip:
   ```bash
   gh issue develop 1208 --base gsgp-arc --name m32/1208-arc-gsgp
   ```

5. **Verify the commits match.** Both lines must print the same SHA. If they don't, stop:
   ```bash
   git rev-parse gsgp-arc
   git rev-parse origin/m32/1208-arc-gsgp
   ```

6. **Rename the local branch and point it at the new remote branch.** The rename works even while a worktree has the branch checked out. Afterwards, the branch still tracks the old remote name, and `gh issue develop` recorded the old branch as its PR base. Fix both:
   ```bash
   git branch -m gsgp-arc m32/1208-arc-gsgp
   git branch --set-upstream-to origin/m32/1208-arc-gsgp m32/1208-arc-gsgp
   git config branch.m32/1208-arc-gsgp.gh-merge-base m32-semantic-gp   # its real parent
   ```
   If a worktree holds the branch, move it to its ghp path, after the in-use checks from "Worktrees" in the main ghp skill: `git worktree move .claude/worktrees/gsgp-arc .claude/worktrees/1208-arc-gsgp`.

7. **Delete the old remote name**, but only when no PR uses it. Deleting a PR's head or base branch closes that PR. Open replacement PRs from the new name first, or keep the old name until they merge:
   ```bash
   gh pr list --head gsgp-arc --state open
   gh pr list --base gsgp-arc --state open
   git push origin --delete gsgp-arc
   ```

8. **Wire the relationships** as for any issue: sub-issue links (`gh issue-ext sub add`) and blockers (`gh issue-ext blocking add`). Report each old name → new name, with its SHA.
