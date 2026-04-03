---
name: ghp:create-template
description: Create a GitHub Project with the standard ghp board layout (Backlog, Todo, In Progress, Review, Done), standard labels, and mark it as a reusable template.
allowed-tools:
  - Bash(gh project *)
  - Bash(gh label *)
  - Bash(gh pm *)
---

# /ghp:create-template — Scaffold a Project Template

Creates a new GitHub Project with the standard ghp configuration and marks it as a template so future projects can be cloned from it.

## Flow

1. **Ask for details** via `AskUserQuestion`:
   - Project name (e.g. "Dev Template")
   - Owner (default: `@me`)

2. **Create the project** (native `gh project` — no gh-pm equivalent for project creation):
   ```bash
   gh project create --owner OWNER --title "Project Name" --format json -q '.number'
   ```

3. **Replace the default Status field** with the 5-stage board (native `gh project` — no gh-pm equivalent for field management). The default Status field (Todo, In Progress, Done) can't be edited — delete and recreate:
   ```bash
   # Get the default Status field ID
   STATUS_ID=$(gh project field-list NUMBER --owner OWNER --format json \
     -q '.fields[] | select(.name == "Status") | .id')

   # Delete it
   gh project field-delete --id "$STATUS_ID"

   # Create with 5 stages
   gh project field-create NUMBER --owner OWNER \
     --name "Status" \
     --data-type "SINGLE_SELECT" \
     --single-select-options "Backlog,Todo,In Progress,Review,Done"
   ```

4. **Create a Priority field:**
   ```bash
   gh project field-create NUMBER --owner OWNER \
     --name "Priority" \
     --data-type "SINGLE_SELECT" \
     --single-select-options "P0 Critical,P1 High,P2 Medium,P3 Low"
   ```

5. **Mark as template:**
   ```bash
   gh project mark-template NUMBER --owner OWNER
   ```

6. **Link project and init gh-pm** (only if `--repo` was provided). This creates `.gh-pm.yml` so all `gh pm` commands work immediately:
   ```bash
   gh project link NUMBER --repo OWNER/REPO --owner OWNER
   gh pm init --project "Project Name" --repo OWNER/REPO
   ```

7. **Ensure standard labels exist** on the repo (if `--repo` was provided):
   ```bash
   gh label create bug --description "Something broken" --color d73a4a --force
   gh label create enhancement --description "Improvement to existing feature" --color a2eeef --force
   gh label create performance --description "Optimization work" --color 0e8a16 --force
   gh label create research --description "Exploration, no guaranteed outcome" --color 5319e7 --force
   gh label create documentation --description "Docs, reports, session logs" --color 0075ca --force
   gh label create testing --description "Test coverage" --color bfd4f2 --force
   gh label create needs-revision --description "References outdated code, needs update" --color fbca04 --force
   ```

8. **Notify the user** with:
   - Project number and URL
   - Reminder to configure built-in Project workflows in the browser (Settings → Workflows):
     - **Auto-add** — automatically adds new issues/PRs
     - **Item closed** — auto-moves to Done
     - **PR merged** — auto-moves to Done
   - Reminder to set up views: Board, Table, Roadmap

## Using a template

To create a new project from this template:
```bash
gh project copy NUMBER --owner OWNER --title "New Project" --drafts
```
