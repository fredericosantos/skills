---
name: ghp:create-template
description: Create a GitHub Project with the standard ghp board layout (Backlog, Todo, In Progress, Review, Done), a Priority field, and standard labels, and mark it as a reusable template.
allowed-tools:
  - Bash(gh project *)
  - Bash(gh pm *)
  - Bash(uv run ${CLAUDE_PLUGIN_ROOT}/scripts/repo-setup.py*)
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

3. **Add the standard Status columns and the Priority field.** The new project's Status field has Todo, In Progress, Done. The script adds Backlog and Review in place, keeping the existing options' ids. It also creates Priority with Critical, High, Medium, Low, which match `.gh-pm.yml`'s `defaults.priority: medium`:
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/repo-setup.py --apply --project NUMBER --owner OWNER --skip-labels
   ```
   It's the same script `/ghp:init` runs on boards that already have items, where deleting and recreating Status would clear every item's status.

4. **Mark as template:**
   ```bash
   gh project mark-template NUMBER --owner OWNER
   ```

5. **Link project and init gh-pm** (only if `--repo` was provided). This creates `.gh-pm.yml` so all `gh pm` commands work immediately. Run it after step 3, so gh-pm maps the new columns and Priority:
   ```bash
   gh project link NUMBER --repo OWNER/REPO --owner OWNER
   gh pm init --project "Project Name" --repo OWNER/REPO
   ```

6. **Ensure standard labels exist** on the repo (only if `--repo` was provided), from its checkout:
   ```bash
   uv run ${CLAUDE_PLUGIN_ROOT}/scripts/repo-setup.py --apply
   ```
   It creates only the roles the repo has no label for, so an existing `docs` fills `documentation` ("Labels" in the main ghp skill). It never recolors or redescribes an existing label.

7. **Notify the user** with:
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
