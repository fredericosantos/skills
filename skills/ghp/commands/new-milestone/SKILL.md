---
name: ghp:new-milestone
description: Create a new milestone with issues, branches, and project tracking in one flow. Plans the work with the user, fills in a YAML plan, and runs a script to create everything on GitHub.
allowed-tools:
  - Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/create-milestone.py *)
  - Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/repo-setup.py*)
---

# /ghp:new-milestone — Create a New Milestone

Plans the work with the user, writes a YAML plan file, and runs `create-milestone.py` to create the milestone, issues, sub-issues, branches, blocking relationships, and project statuses — all in one script call.

## Flow

1. **Ask for details** via `AskUserQuestion`:
   - Milestone title (e.g. "New Eval Strategy")
   - Brief description of the goal
   - Whether to plan issues now or just create the milestone

2. **Plan issues with the user.** Discuss the work breakdown:
   - What issues are needed (features, fixes, tests, docs)
   - Which issues have sub-issues
   - Blocking relationships between issues
   - Labels for each issue

   Write the full issue content — title, body (using the issue template from the main ghp skill), labels, and relationships.

3. **Fill in the YAML plan.** Copy the template at `${CLAUDE_PLUGIN_ROOT}/assets/milestone-template.yml` to a scratch location outside the repo, so it never gets committed, and fill it in. Each issue and sub-issue gets a local `id` (integer) used only within the YAML to express `blocked_by` relationships — the script maps these to real GitHub issue numbers. Labels and statuses use ghp's names: the script maps them to the repo's own.

4. **Dry-run the script.** It reads the repo, its labels and its board, and prints every write without running it:
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/create-milestone.py plan.yml --dry-run
   ```
   A label, status or priority the repo doesn't have stops it with a list of problems and nothing created. Fix the plan, or add what's missing with `uv run ${CLAUDE_PLUGIN_ROOT}/scripts/repo-setup.py --apply` after the user agrees.

5. **Run the script** with the same command without `--dry-run`. It:
   - Creates the milestone, reads back the number GitHub assigned, and renames it `Milestone {N} - {Title}`
   - Creates the milestone base `m{N}-{slug}` on GitHub from the default branch's tip, without touching the local checkout
   - Creates all issues and sub-issues as separate GitHub issues and adds each to the Project
   - Links sub-issues via `gh issue-ext sub add`
   - Sets blocking relationships via `gh issue-ext blocking add`
   - Creates each linked branch from its parent via `gh issue develop --base`
   - Sets project status and priority via `gh pm move`
   - Prints a summary with the local-to-GitHub ID mapping

6. **Record decisions.** For each issue whose planning settled questions with the user, post a plan record on it ("Plan record" in the main ghp skill).

7. **Create TaskList** from the script output. Sub-issues first, parent issues last:
   ```
   TaskCreate: "#{child} — {child title}"
   TaskCreate: "#{parent} — {parent title} (parent — wrap up when sub-issues done)"
   ```

8. **Start working.** Run `/ghp:work` on the first issue. It opens the issue's branch in its own worktree.

## Notes

- Issue bodies follow the template: Summary, Changes Required, Dependencies, Acceptance Criteria
- Status assignment: first issue → In Progress, unblocked → Todo, blocked → Backlog
- The YAML template is at `${CLAUDE_PLUGIN_ROOT}/assets/milestone-template.yml`
- The script is at `${CLAUDE_PLUGIN_ROOT}/scripts/create-milestone.py`
