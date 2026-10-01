"""Shared helpers for the ghp scripts: running gh, reading .gh-pm.yml, resolving labels and board options."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

GH_PM_CONFIG = ".gh-pm.yml"


@dataclass(frozen=True)
class LabelRole:
    name: str
    synonyms: tuple[str, ...]
    description: str
    color: str


# A repo label whose name is one of a role's synonyms fills that role.
LABEL_ROLES = (
    LabelRole("bug", ("bug",), "Something broken", "d73a4a"),
    LabelRole("enhancement", ("enhancement",), "Improvement to existing feature", "a2eeef"),
    LabelRole("performance", ("performance", "perf"), "Optimization work", "0e8a16"),
    LabelRole("research", ("research",), "Exploration, no guaranteed outcome", "5319e7"),
    LabelRole("documentation", ("documentation", "docs"), "Docs, reports, session logs", "0075ca"),
    LabelRole("testing", ("testing", "test", "tests"), "Test coverage", "bfd4f2"),
    LabelRole("needs-revision", ("needs-revision",), "References outdated code, needs update", "fbca04"),
)

# The standard board in column order, with the option names that count as each column.
STATUS_STAGES: dict[str, tuple[str, ...]] = {
    "Backlog": ("Backlog",),
    "Todo": ("Todo",),
    "In Progress": ("In Progress",),
    "Review": ("Review", "In Review"),
    "Done": ("Done",),
}
NEW_STATUS_COLORS = {"Backlog": "GRAY", "Todo": "GREEN", "In Progress": "YELLOW", "Review": "BLUE", "Done": "PURPLE"}

PRIORITY_FIELD = "Priority"
PRIORITY_OPTIONS = ("Critical", "High", "Medium", "Low")


def run(args: list[str], *, stdin: str | None = None) -> str:
    """Run a command and return its stdout; on failure print the command and stderr, then exit."""
    result = subprocess.run(args, input=stdin, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"ERROR: {shlex.join(args)}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


class Runner:
    """Always runs reads; in a dry run, prints writes instead of running them."""

    def __init__(self, *, dry_run: bool) -> None:
        self.dry_run = dry_run

    def read(self, *args: str, stdin: str | None = None) -> str:
        return run(list(args), stdin=stdin)

    def write(self, *args: str, stdin: str | None = None, dry_output: str = "") -> str:
        if self.dry_run:
            print(f"  [dry-run] {shlex.join(args)}")
            return dry_output
        return run(list(args), stdin=stdin)


def repo_labels(runner: Runner) -> list[str]:
    output = runner.read("gh", "label", "list", "--json", "name", "--limit", "1000")
    return [label["name"] for label in json.loads(output)]


def project_fields(runner: Runner, number: str, owner: str) -> list[dict[str, Any]]:
    output = runner.read("gh", "project", "field-list", number, "--owner", owner, "--format", "json")
    return json.loads(output)["fields"]


def gh_pm_key(option_name: str) -> str:
    """The key gh-pm derives from a project option name ("In Review" -> "in_review")."""
    return option_name.lower().replace(" ", "_")


def find_gh_pm_config(start: Path) -> Path | None:
    """Find .gh-pm.yml in `start` or a parent directory, the way gh-pm does."""
    for directory in (start, *start.parents):
        candidate = directory / GH_PM_CONFIG
        if candidate.is_file():
            return candidate
    return None


def load_gh_pm_config(start: Path) -> dict[str, Any]:
    path = find_gh_pm_config(start)
    if path is None:
        sys.exit(f"ERROR: no {GH_PM_CONFIG} in {start} or its parents. Run /ghp:init first.")
    return yaml.safe_load(path.read_text())


def project_owner(gh_pm: dict[str, Any], repo_owner: str) -> str:
    project = gh_pm["project"]
    # gh-pm leaves owner unset for some user projects and then resolves them against the repo owner.
    return project.get("owner") or project.get("org") or repo_owner


def resolve_label(name: str, repo_labels: list[str]) -> str | None:
    """The repo's label for `name`: the label itself, or the repo's label for the same role."""
    by_lower = {label.lower(): label for label in repo_labels}
    if name.lower() in by_lower:
        return by_lower[name.lower()]
    for role in LABEL_ROLES:
        if name.lower() in role.synonyms:
            for synonym in role.synonyms:
                if synonym in by_lower:
                    return by_lower[synonym]
    return None


def stage_of(option_name: str) -> str | None:
    """The standard board column an option name counts as, if any."""
    for stage, names in STATUS_STAGES.items():
        if option_name.lower() in {name.lower() for name in names}:
            return stage
    return None


def resolve_status(value: str, status_values: dict[str, str]) -> str | None:
    """The repo's gh-pm Status key for `value`: a gh-pm key, or a column key such as `review`."""
    if value in status_values:
        return value
    for stage in STATUS_STAGES:
        if gh_pm_key(stage) == value:
            for key, option_name in status_values.items():
                if stage_of(option_name) == stage:
                    return key
    return None


def resolve_priority(value: str, priority_values: dict[str, str]) -> str | None:
    """The repo's gh-pm Priority key for `value` (`critical`, `high`, `medium`, `low`)."""
    return value if value in priority_values else None


def plan_status_options(existing: list[dict[str, str]]) -> list[dict[str, str]]:
    """The existing options, unchanged and in order, plus each missing column before the next column present."""
    options = [dict(option) for option in existing]
    stages = list(STATUS_STAGES)
    for i, stage in enumerate(stages):
        if any(stage_of(option["name"]) == stage for option in options):
            continue
        later = set(stages[i + 1 :])
        position = next((j for j, option in enumerate(options) if stage_of(option["name"]) in later), len(options))
        options.insert(position, {"name": stage, "color": NEW_STATUS_COLORS[stage], "description": ""})
    return options


def single_select(fields: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    """A single-select field from `gh project field-list --format json` output, by name."""
    for field in fields:
        if field["name"] == name and field["type"] == "ProjectV2SingleSelectField":
            return field
    return None
