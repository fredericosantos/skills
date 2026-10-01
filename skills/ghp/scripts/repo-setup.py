# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Check a repo and its Project against ghp's labels, board columns and Priority field.

Without --apply it only reports, printing the commands it would run. With --apply it creates what is
missing. It never renames, recolors or deletes anything. Missing Status options are added in place:
every existing option is sent back with its id, so items keep their values.

Usage:
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/repo-setup.py [--apply] [--project N --owner OWNER] [--skip-labels]
"""

from __future__ import annotations

import argparse
import json
import shlex
import sys
from pathlib import Path
from typing import Any

from ghp_common import (
    LABEL_ROLES,
    PRIORITY_FIELD,
    PRIORITY_OPTIONS,
    STATUS_STAGES,
    Runner,
    find_gh_pm_config,
    load_gh_pm_config,
    plan_status_options,
    project_fields,
    project_owner,
    repo_labels,
    resolve_label,
    single_select,
    stage_of,
)

OPTIONS_QUERY = """
query($id: ID!) {
  node(id: $id) { ... on ProjectV2SingleSelectField { options { id name color description } } }
}"""

UPDATE_OPTIONS_MUTATION = """
mutation($fieldId: ID!, $options: [ProjectV2SingleSelectFieldOptionInput!]) {
  updateProjectV2Field(input: {fieldId: $fieldId, singleSelectOptions: $options}) {
    projectV2Field { ... on ProjectV2SingleSelectField { options { id name } } }
  }
}"""


def check_labels(runner: Runner, gh_pm: dict[str, Any] | None) -> list[str]:
    """Report each ghp label role's label in this repo; create the ones with no match. Returns what's missing."""
    labels = repo_labels(runner)
    print("Labels (ghp role -> repo label):")
    missing: list[str] = []
    for role in LABEL_ROLES:
        found = resolve_label(role.name, labels)
        print(f"  {role.name:<15} -> {found or 'MISSING'}")
        if found is None:
            missing.append(role.name)
            runner.write("gh", "label", "create", role.name, "--description", role.description, "--color", role.color)
    # gh pm create applies these verbatim, and fails when one doesn't exist.
    defaults = gh_pm["defaults"]["labels"] if gh_pm else []
    lower = {label.lower() for label in labels}
    for name in defaults:
        if name.lower() not in lower:
            print(f"  {name:<15} -> MISSING (.gh-pm.yml defaults.labels)")
            missing.append(name)
            runner.write("gh", "label", "create", name, "--description", "Applied by gh pm create", "--color", "ededed")
    return missing


def check_status(runner: Runner, fields: list[dict[str, Any]]) -> list[str]:
    """Report the board's Status options against the standard columns; add missing ones keeping existing ids."""
    field = single_select(fields, "Status")
    if field is None:
        sys.exit("ERROR: the Project has no Status field")
    payload = json.dumps({"query": OPTIONS_QUERY, "variables": {"id": field["id"]}})
    existing = json.loads(runner.read("gh", "api", "graphql", "--input", "-", stdin=payload))["data"]["node"]["options"]
    print("Status columns (standard -> board option):")
    missing = []
    for stage in STATUS_STAGES:
        found = next((option["name"] for option in existing if stage_of(option["name"]) == stage), None)
        print(f"  {stage:<15} -> {found or 'MISSING'}")
        if found is None:
            missing.append(stage)
    if not missing:
        return []

    planned = plan_status_options(existing)
    print(f"  will set options to: {', '.join(option['name'] for option in planned)} (existing ids kept)")
    mutation = json.dumps({"query": UPDATE_OPTIONS_MUTATION, "variables": {"fieldId": field["id"], "options": planned}})
    output = runner.write("gh", "api", "graphql", "--input", "-", stdin=mutation)
    if not runner.dry_run:
        after = json.loads(output)["data"]["updateProjectV2Field"]["projectV2Field"]["options"]
        kept = {option["id"]: option["name"] for option in after}
        changed = [option["name"] for option in existing if kept.get(option["id"]) != option["name"]]
        if changed:
            sys.exit(f"ERROR: the update changed the ids of {changed}; items with those values may have lost them")
        print(f"  verified: all {len(existing)} existing option ids kept")
    return missing


def check_priority(runner: Runner, fields: list[dict[str, Any]], number: str, owner: str) -> list[str]:
    """Report the Priority field; create it with the standard options when the board has none."""
    field = single_select(fields, PRIORITY_FIELD)
    if field is not None:
        print(f"Priority field: {', '.join(option['name'] for option in field['options'])}")
        return []
    print(f"Priority field: MISSING (will create: {', '.join(PRIORITY_OPTIONS)})")
    runner.write(
        *("gh", "project", "field-create", number, "--owner", owner, "--name", PRIORITY_FIELD),
        *("--data-type", "SINGLE_SELECT", "--single-select-options", ",".join(PRIORITY_OPTIONS)),
    )
    return [PRIORITY_FIELD]


def stale_mappings(gh_pm: dict[str, Any], fields: list[dict[str, Any]]) -> list[str]:
    """Board options gh-pm can't set yet: not in fields.*.values, or not in its cached metadata."""
    cached_fields = (gh_pm.get("metadata") or {}).get("fields") or []
    cached = {field["name"]: {option["id"] for option in field.get("options") or []} for field in cached_fields}
    stale = []
    for config_key, field_name in (("status", "Status"), ("priority", PRIORITY_FIELD)):
        field = single_select(fields, field_name)
        if field is None:
            continue
        mapping = (gh_pm.get("fields") or {}).get(config_key)
        mapped = set(mapping["values"].values()) if mapping else set()
        for option in field["options"]:
            # gh pm create reads option ids from the cache whenever one exists.
            if option["name"] not in mapped or (cached and option["id"] not in cached.get(field_name, set())):
                stale.append(f"{field_name}: {option['name']}")
    return stale


def main(argv: list[str] | None = None, runner: Runner | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--apply", action="store_true", help="create what is missing (default: report only)")
    parser.add_argument("--project", help="Project number (default: from .gh-pm.yml)")
    parser.add_argument("--owner", help="Project owner (default: from .gh-pm.yml)")
    parser.add_argument("--skip-labels", action="store_true", help="skip the label check, e.g. outside a repo")
    args = parser.parse_args(argv)

    if bool(args.project) != bool(args.owner):
        parser.error("--project and --owner go together")
    runner = runner or Runner(dry_run=not args.apply)
    gh_pm = load_gh_pm_config(Path.cwd()) if find_gh_pm_config(Path.cwd()) else None
    if args.project:
        number, owner = args.project, args.owner
        if gh_pm and str(gh_pm["project"]["number"]) != number:
            gh_pm = None  # this .gh-pm.yml describes another project
    elif gh_pm:
        repo = json.loads(runner.read("gh", "repo", "view", "--json", "nameWithOwner"))["nameWithOwner"]
        number, owner = str(gh_pm["project"]["number"]), project_owner(gh_pm, repo.split("/")[0])
    else:
        sys.exit("ERROR: no .gh-pm.yml here or above; pass --project and --owner")

    missing = [] if args.skip_labels else check_labels(runner, gh_pm)
    fields = project_fields(runner, number, owner)
    missing += check_status(runner, fields)
    missing += check_priority(runner, fields, number, owner)

    if missing and not runner.dry_run:
        fields = project_fields(runner, number, owner)
    stale = stale_mappings(gh_pm, fields) if gh_pm else []

    if missing and runner.dry_run:
        print(f"\nMissing: {', '.join(missing)}. Re-run with --apply to create them.")
    elif missing:
        print(f"\nCreated: {', '.join(missing)}.")
    if gh_pm and stale:
        repos = ",".join(gh_pm["repositories"])
        refresh = ["gh", "pm", "init", "--project", gh_pm["project"]["name"], "--repo", repos]
        print(f"\n.gh-pm.yml doesn't know {', '.join(stale)}. Refresh it, then review the diff:")
        print(f"  echo y | {shlex.join(refresh)} --interactive=false")
    if not missing and not stale:
        print("\nThe repo matches the ghp setup.")


if __name__ == "__main__":
    main()
