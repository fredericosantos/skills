---
name: ghp:new-milestone
description: Create a new milestone with issues, branches, and project tracking in one flow. Plans the work, creates the milestone and branch, then delegates issue creation to a haiku subagent.
allowed-tools:
  - Bash(gh milestone *)
  - Bash(gh issue *)
  - Bash(gh pm *)
  - Bash(git checkout *)
  - Bash(git push *)
---

# /ghp:new-milestone — Create a New Milestone

Creates a milestone, its branch, plans issues, and delegates creation to a haiku subagent — all in one flow.

## Flow

1. **Ask for details** via `AskUserQuestion`:
   - Milestone title (e.g. "New Eval Strategy")
   - Brief description of the goal
   - Whether to plan issues now or just create the milestone

2. **Create the milestone:**
   ```bash
   gh milestone create --title "Milestone {N} - {Title}"
   ```
   The milestone number `{N}` is the number GitHub assigns on creation.

3. **Create the milestone branch** and push it:
   ```bash
   git checkout -b m{N}-{short-name}
   git push -u origin m{N}-{short-name}
   ```

4. **Plan issues with the user.** Discuss the work breakdown:
   - What issues are needed (features, fixes, tests, docs)
   - Which issues have sub-issues
   - Blocking relationships between issues
   - Labels for each issue

   Write the full issue content — title, body (using the issue template from the main ghp skill), labels, and relationships.

5. **Delegate to haiku subagent.** Send a single prompt with all the work:

   ```
   Create these issues on GitHub for repo OWNER/REPO:

   1. Issue: "{title}" — label: {label}, milestone: "Milestone {N} - {Title}"
      Body: [full body text]
      Sub-issues:
        a. "{sub-title}" — label: {label}
           Body: [full body text]

   2. Set up sub-issue relationships: gh issue-ext sub add {parent} {child}
   3. Set up blocking relationships: gh issue-ext blocking add {blocked} {blocker}
   4. Create linked issue branches:
      gh issue-ext branch create {number} --name m{N}-{short-name}/{tag}/{number}-{desc}
   5. Set project status:
      gh pm move {number} --status in_progress  (first issue to work on)
      gh pm move {number} --status todo          (unblocked issues)
      gh pm move {number} --status backlog       (blocked issues)
   ```

   The primary agent starts working immediately after delegation, without waiting for the subagent to finish.

6. **Create TaskList** from the planned issues. Sub-issues first, parent issues last:
   ```
   TaskCreate: "#{child} — {child title}"
   TaskCreate: "#{parent} — {parent title} (parent — wrap up when sub-issues done)"
   ```

7. **Start working.** Check out the first issue's branch and begin implementation.

## Notes

- The haiku subagent only executes — it does not decide what to implement
- Issue bodies follow the template: Summary, Changes Required, Dependencies, Acceptance Criteria
- Status assignment: first issue → In Progress, unblocked → Todo, blocked → Backlog
