---
name: ghp:new-milestone
description: Create a new milestone with issues, branches, and project tracking in one flow. Plans the work with the user, fills in a YAML plan, and runs a script to create everything on GitHub.
allowed-tools:
  - Bash(python skills/ghp/scripts/create-milestone.py *)
  - Bash(git checkout *)
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

3. **Fill in the YAML plan.** Read the template at `skills/ghp/assets/milestone-template.yml` and create a filled-in copy (e.g. `plan.yml` in the repo root or a temp location). Each issue and sub-issue gets a local `id` (integer) used only within the YAML to express `blocked_by` relationships — the script maps these to real GitHub issue numbers.

4. **Run the script:**
   ```bash
   python skills/ghp/scripts/create-milestone.py plan.yml
   ```

   The script handles everything:
   - Creates the milestone with `Milestone {N} - {Title}` naming
   - Creates and pushes the milestone branch `m{N}-{slug}`
   - Creates all issues and sub-issues as separate GitHub issues
   - Links sub-issues via `gh issue-ext sub add`
   - Sets blocking relationships via `gh issue-ext blocking add`
   - Creates linked branches via `gh issue-ext branch create`
   - Sets project statuses via `gh pm move`
   - Prints a summary with the local-to-GitHub ID mapping

5. **Create TaskList** from the script output. Sub-issues first, parent issues last:
   ```
   TaskCreate: "#{child} — {child title}"
   TaskCreate: "#{parent} — {parent title} (parent — wrap up when sub-issues done)"
   ```

6. **Start working.** Check out the first issue's branch and begin implementation.

## Notes

- Issue bodies follow the template: Summary, Changes Required, Dependencies, Acceptance Criteria
- Status assignment: first issue → In Progress, unblocked → Todo, blocked → Backlog
- The YAML template is at `skills/ghp/assets/milestone-template.yml`
- The script is at `skills/ghp/scripts/create-milestone.py`
