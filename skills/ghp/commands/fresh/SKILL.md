---
name: ghp:fresh
description: Bootstrap a fresh agent (new conversation or subagent) onto a specific issue or let it pick from Todo. Loads full context — issue details, sub-issues, blocking, branch, worktree, plan record — and starts working immediately. Use this when spinning up a new agent or starting a fresh conversation on a known issue.
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
   gh issue-ext sub list 42      # sub-issues
   gh issue-ext blocking list 42 # blockers
   gh issue develop --list 42    # linked branch
   ```

2. **Check blockers.** If the issue has unresolved blockers, warn the user and ask whether to proceed or pick a different issue.

3. **Move to In Progress:**
   ```bash
   gh pm move 42 --status in_progress
   ```

4. **Open the issue's worktree.** Follow `/ghp:work` steps 5–7: find or create the linked branch, add its worktree under `.claude/worktrees/`, and run the repo's `worktree_setup`.

5. **Read the plan record.** The newest issue comment that starts with `## Plan record` holds the approved plan and the user's decisions ("Plan record" in the main ghp skill). Older issues may have a `## Plan` comment instead.
   ```bash
   gh issue view 42 --json comments -q '[.comments[] | select(.body | startswith("## Plan"))] | last | .body'
   ```

6. **Build the brief.** When handing the issue to a subagent, give it this brief, filled from steps 1–5. When working yourself, read it back before starting:
   ```
   Issue #42 — <title> (<milestone>)
   Branch: m7/42-batch-tree-eval, from m7-new-eval-strategy
   Worktree: <absolute path>/.claude/worktrees/42-batch-tree-eval (work only here)
   Goal: <Summary from the issue body>
   Plan: <the plan record's Plan, verbatim>
   Decided already (don't re-ask): <the plan record's Decisions, verbatim>
   Acceptance criteria: <from the issue body>
   Sub-issues: <#N state, ...>. Blocked by: <#N or none>
   Finish with /ghp:wrap-issue.
   ```
   If there is no plan record, say so in the brief rather than inventing a plan.

7. **Create TaskList.** If the issue has sub-issues, create tasks from them (sub-issues first, parent last). If no sub-issues, create a single task for the issue.

8. **Start working** in the worktree, from the issue body and the plan record.

### Without issue number: `/ghp:fresh`

1. **Fetch Todo issues:**
   ```bash
   gh pm list --status todo
   ```

2. **Check blocking status** for each Todo issue to find which are unblocked.

3. **Present unblocked Todo issues** to the user via `AskUserQuestion` (up to 4 options, sorted by milestone first, then standalone).

4. **Continue with the selected issue** — follow the "With issue number" flow above from step 1.
