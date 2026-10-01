# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Create a milestone with issues, sub-issues, linked branches, and project tracking.

Reads a YAML plan file and executes all GitHub CLI commands in the right order. Every check runs
before the first write, so a label or status the repo doesn't have fails with nothing created.

Usage:
    uv run ${CLAUDE_PLUGIN_ROOT}/scripts/create-milestone.py <plan.yml> [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from ghp_common import (
    Runner,
    gh_pm_key,
    load_gh_pm_config,
    project_fields,
    project_owner,
    repo_labels,
    resolve_label,
    resolve_priority,
    resolve_status,
    single_select,
)


@dataclass(frozen=True)
class Item:
    id: int
    title: str
    label: str
    status: str
    body: str
    blocked_by: tuple[int, ...]
    priority: str | None
    parent: int | None  # local id of the parent issue, for a sub-issue


@dataclass(frozen=True)
class Context:
    repo: str
    default_branch: str
    project_number: str
    project_owner: str
    labels: dict[int, str]  # local id -> repo label
    statuses: dict[int, str]  # local id -> gh-pm Status key
    priorities: dict[int, str]  # local id -> gh-pm Priority key


def slugify(text: str) -> str:
    """Convert text to a branch-name-safe slug."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def extract_number(output: str, kind: str) -> str:
    """Extract the number from a gh URL such as .../issues/42 or .../milestone/7."""
    match = re.search(rf"/{kind}/(\d+)", output)
    if not match:
        sys.exit(f"ERROR: could not find a /{kind}/<number> URL in: {output}")
    return match.group(1)


def load_plan(path: Path) -> tuple[dict[str, Any], list[Item]]:
    """Read the plan; issues come before their sub-issues. Exits listing every structural problem."""
    plan = yaml.safe_load(path.read_text())
    items: list[Item] = []
    problems: list[str] = []

    def make(entry: dict[str, Any], parent: int | None) -> None:
        missing = [key for key in ("id", "title", "label", "status") if entry.get(key) in (None, "")]
        if missing:
            problems.append(f"item {entry.get('id', '?')}: missing {', '.join(missing)}")
            return
        items.append(
            Item(
                id=entry["id"],
                title=entry["title"],
                label=entry["label"],
                status=entry["status"],
                body=entry.get("body") or "",
                blocked_by=tuple(entry.get("blocked_by") or ()),
                priority=entry.get("priority"),
                parent=parent,
            )
        )

    for issue in plan.get("issues") or []:
        make(issue, parent=None)
        for sub in issue.get("sub_issues") or []:
            make(sub, parent=issue.get("id"))

    if not (plan.get("milestone") or {}).get("title"):
        problems.append("milestone.title is empty")
    ids = [item.id for item in items]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    if duplicates:
        problems.append(f"duplicate ids: {duplicates}")
    for item in items:
        unknown = [b for b in item.blocked_by if b not in ids]
        if unknown:
            problems.append(f"item {item.id}: blocked_by unknown ids {unknown}")
    if problems:
        sys.exit("ERROR: invalid plan:\n  " + "\n  ".join(problems))
    return plan, items


def preflight(items: list[Item], runner: Runner) -> Context:
    """Read the repo, its labels and its board; exit listing every problem before anything is created."""
    repo_info = json.loads(runner.read("gh", "repo", "view", "--json", "nameWithOwner,defaultBranchRef"))
    repo = repo_info["nameWithOwner"]
    gh_pm = load_gh_pm_config(Path.cwd())
    number = str(gh_pm["project"]["number"])
    owner = project_owner(gh_pm, repo.split("/")[0])
    labels_in_repo = repo_labels(runner)
    fields = project_fields(runner, number, owner)
    problems: list[str] = []

    labels: dict[int, str] = {}
    for item in items:
        resolved = resolve_label(item.label, labels_in_repo)
        if resolved is None:
            problems.append(f"item {item.id}: label {item.label!r} has no match or synonym among {repo}'s labels")
        else:
            labels[item.id] = resolved

    statuses = resolve_options(
        {item.id: item.status for item in items}, "status", "Status", gh_pm, fields, resolve_status, problems
    )
    default_priority = gh_pm["defaults"].get("priority")
    wanted_priorities = {item.id: item.priority or default_priority for item in items}
    priorities = resolve_options(
        {i: p for i, p in wanted_priorities.items() if p},
        "priority",
        "Priority",
        gh_pm,
        fields,
        resolve_priority,
        problems,
    )

    if problems:
        sys.exit("ERROR: nothing was created:\n  " + "\n  ".join(problems))
    return Context(repo, repo_info["defaultBranchRef"]["name"], number, owner, labels, statuses, priorities)


def resolve_options(
    wanted: dict[int, str],
    config_key: str,
    field_name: str,
    gh_pm: dict[str, Any],
    fields: list[dict[str, Any]],
    resolver: Callable[[str, dict[str, str]], str | None],
    problems: list[str],
) -> dict[int, str]:
    """Map each item's value to a gh-pm key whose option exists on the board; record a problem otherwise."""
    if not wanted:
        return {}
    field = single_select(fields, field_name)
    if field is None:
        problems.append(f"the board has no {field_name} field; create it with repo-setup.py --apply")
        return {}
    mapping = (gh_pm.get("fields") or {}).get(config_key)
    if mapping is None:
        problems.append(f".gh-pm.yml has no fields.{config_key} mapping; refresh it (see /ghp:init)")
        return {}
    values = mapping["values"]
    live = [option["name"] for option in field["options"]]
    live_values = {gh_pm_key(name): name for name in live}
    resolved: dict[int, str] = {}
    for item_id, value in wanted.items():
        key = resolver(value, values)
        if key is not None and values[key] in live:
            resolved[item_id] = key
        elif resolver(value, live_values) is not None:
            problems.append(
                f"item {item_id}: {config_key} {value!r} is on the board but .gh-pm.yml is stale; refresh it (see /ghp:init)"
            )
        else:
            problems.append(
                f"item {item_id}: {config_key} {value!r} is not a {field_name} option {live}; "
                "add it with repo-setup.py --apply or use an existing one"
            )
    return resolved


def create(plan: dict[str, Any], items: list[Item], ctx: Context, runner: Runner) -> None:
    title = plan["milestone"]["title"]
    description = plan["milestone"].get("description") or ""

    # --- Step 1: Create the milestone, then name it after the number GitHub assigned ---
    args = ["gh", "milestone", "create", "--title", title]
    if description:
        args += ["--description", description]
    milestone_number = extract_number(
        runner.write(*args, dry_output=f"https://github.com/{ctx.repo}/milestone/0"), "milestone"
    )
    if not runner.dry_run:
        assigned = runner.read("gh", "api", f"repos/{ctx.repo}/milestones/{milestone_number}", "--jq", ".title")
        if assigned != title:
            sys.exit(f"ERROR: milestone #{milestone_number} is {assigned!r}, expected {title!r}")
    milestone_name = f"Milestone {milestone_number} - {title}"
    runner.write("gh", "milestone", "edit", milestone_number, "--title", milestone_name)
    print(f"Created milestone: {milestone_name}")

    # --- Step 2: Create the milestone base from the default branch's remote tip ---
    base = plan.get("branch") or f"m{milestone_number}-{slugify(title)}"
    sha = runner.read("gh", "api", f"repos/{ctx.repo}/git/ref/heads/{ctx.default_branch}", "--jq", ".object.sha")
    runner.write("gh", "api", f"repos/{ctx.repo}/git/refs", "-f", f"ref=refs/heads/{base}", "-f", f"sha={sha}")
    runner.write("git", "fetch", "origin", base)
    print(f"Created branch: {base} (from {ctx.default_branch} @ {sha[:8]})")

    # --- Step 3: Create all issues and add them to the project ---
    numbers: dict[int, str] = {}
    for item in items:
        url = runner.write(
            *("gh", "issue", "create", "--title", item.title, "--label", ctx.labels[item.id]),
            *("--milestone", milestone_name, "--body", item.body),
            dry_output=f"https://github.com/{ctx.repo}/issues/{item.id}",
        )
        numbers[item.id] = extract_number(url, "issues")
        runner.write("gh", "project", "item-add", ctx.project_number, "--owner", ctx.project_owner, "--url", url)
        print(f"  Created #{numbers[item.id]}: {item.title}")

    # --- Step 4: Link sub-issues ---
    print("\nLinking sub-issues...")
    for item in items:
        if item.parent is not None:
            runner.write("gh", "issue-ext", "sub", "add", numbers[item.parent], numbers[item.id])
            print(f"  #{numbers[item.id]} is sub-issue of #{numbers[item.parent]}")

    # --- Step 5: Set blocking relationships ---
    print("\nSetting blocking relationships...")
    for item in items:
        for blocker in item.blocked_by:
            runner.write("gh", "issue-ext", "blocking", "add", numbers[item.id], numbers[blocker])
            print(f"  #{numbers[item.id]} is blocked by #{numbers[blocker]}")

    # --- Step 6: Create linked branches, each from its parent branch ---
    # m{N}/ prefix, not the full base name: a ref can't be both a branch and a directory.
    print("\nCreating linked branches...")
    branches: dict[int, str] = {}
    for item in items:
        if item.parent is None:
            name, parent_branch = f"m{milestone_number}/{numbers[item.id]}-{slugify(item.title)}", base
        else:
            parent = numbers[item.parent]
            name = f"m{milestone_number}/{parent}/{numbers[item.id]}-{slugify(item.title)}"
            parent_branch = branches[item.parent]
        runner.write("gh", "issue", "develop", numbers[item.id], "--base", parent_branch, "--name", name)
        branches[item.id] = name
        print(f"  #{numbers[item.id]} -> {name} (from {parent_branch})")

    # --- Step 7: Set project status and priority ---
    print("\nSetting project fields...")
    for item in items:
        args = ["gh", "pm", "move", numbers[item.id], "--status", ctx.statuses[item.id]]
        if item.id in ctx.priorities:
            args += ["--priority", ctx.priorities[item.id]]
        runner.write(*args)
        print(f"  #{numbers[item.id]} -> {ctx.statuses[item.id]}, priority {ctx.priorities.get(item.id, '-')}")

    # --- Summary ---
    print(f"\nDone! Milestone: {milestone_name} (#{milestone_number})")
    print(f"Branch: {base}")
    print(f"Issues created: {len(numbers)}")
    print("ID mapping (local -> GitHub):")
    for local_id, gh_number in sorted(numbers.items()):
        print(f"  {local_id} -> #{gh_number}  {branches[local_id]}")


def main(argv: list[str] | None = None, runner: Runner | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("plan", type=Path)
    parser.add_argument(
        "--dry-run", action="store_true", help="run the checks and print the writes without running them"
    )
    args = parser.parse_args(argv)
    if not args.plan.exists():
        sys.exit(f"ERROR: {args.plan} not found")

    runner = runner or Runner(dry_run=args.dry_run)
    if runner.dry_run:
        print("DRY RUN: nothing is created. The milestone shows as #0 and issues as their plan ids.\n")
    plan, items = load_plan(args.plan)
    ctx = preflight(items, runner)
    create(plan, items, ctx, runner)


if __name__ == "__main__":
    main()
