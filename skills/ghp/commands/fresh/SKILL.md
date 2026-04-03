---
name: ghp:fresh
description: Bootstrap a fresh agent (new conversation or subagent) onto a specific issue or let it pick from Todo. Loads full context — issue details, sub-issues, blocking, branch, plan — and starts working immediately. Use this when spinning up a new agent or starting a fresh conversation on a known issue.
allowed-tools:
  - Bash(gh issue *)
  - Bash(gh issue-ext *)
  - Bash(gh pm *)
  - Bash(git *)
---

# /ghp:fresh — Bootstrap a Fresh Agent

Loads all context needed to work on an issue and starts immediately. Designed for fresh conversations and subagents that have no prior context.

## Flow

### With issue number: `/ghp:fresh 42`

1. **Fetch issue details:**
   ```bash
   gh issue view 42 --json title,body,state,labels,milestone
   gh issue-ext show 42          # sub-issues, blocking, branches
   gh issue-ext sub list 42      # sub-issues
   gh issue-ext blocking list 42 # blockers
   gh issue-ext branch list 42   # linked branch
   ```

2. **Check blockers.** If the issue has unresolved blockers, warn the user and ask whether to proceed or pick a different issue.

3. **Move to In Progress:**
   ```bash
   gh pm move 42 --status in_progress
   ```

4. **Check out the linked branch.** Use the branch from `gh issue-ext branch list`. If no branch exists, create one following the naming convention:
   - Under a milestone: `m{N}/{issue}-{slug}`
   - Standalone: `{issue}-{slug}`

5. **Read plan comments.** Check for plan comments on the issue:
   ```bash
   gh issue view 42 --json comments -q '.comments[].body'
   ```
   Look for comments starting with `## Plan` — these contain implementation plans from previous sessions.

6. **Create TaskList.** If the issue has sub-issues, create tasks from them (sub-issues first, parent last). If no sub-issues, create a single task for the issue.

7. **Start working.** Begin implementation based on the issue body and any plan comments.

### Without issue number: `/ghp:fresh`

1. **Fetch Todo issues:**
   ```bash
   gh pm list --status todo
   ```

2. **Check blocking status** for each Todo issue to find which are unblocked.

3. **Present unblocked Todo issues** to the user via `AskUserQuestion` (up to 4 options, sorted by milestone first, then standalone).

4. **Continue with the selected issue** — follow the "With issue number" flow above from step 1.
