"""Tests for the ghp scripts: create-milestone.py, repo-setup.py and ghp_common.py."""

from __future__ import annotations

import importlib.util
import json
import sys
import textwrap
from pathlib import Path

import pytest

GHP = Path(__file__).parent.parent / "skills" / "ghp"
sys.path.insert(0, str(GHP / "scripts"))

import ghp_common  # noqa: E402


def load_script(name: str):
    """Load a script despite its hyphenated filename."""
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), GHP / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


cm = load_script("create-milestone")
rs = load_script("repo-setup")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

GH_PM_YML = """\
project:
    name: fsgp
    number: 7
    owner: octo
repositories:
    - octo/repo
defaults:
    priority: medium
    status: todo
    labels: []
fields:
    priority:
        field: Priority
        values: {critical: Critical, high: High, medium: Medium, low: Low}
    status:
        field: Status
        values: {todo: Todo, in_progress: In Progress, in_review: In Review, done: Done}
"""

STATUS_OPTIONS = [
    {"id": "s1", "name": "Todo", "color": "GREEN", "description": "not started"},
    {"id": "s2", "name": "In Progress", "color": "YELLOW", "description": "active"},
    {"id": "s3", "name": "In Review", "color": "BLUE", "description": ""},
    {"id": "s4", "name": "Done", "color": "PURPLE", "description": "completed"},
]
PRIORITY_OPTIONS = [{"id": f"p{i}", "name": name} for i, name in enumerate(["Critical", "High", "Medium", "Low"])]


def field_list(*, priority: bool = True, status: list[dict] = STATUS_OPTIONS) -> str:
    fields = [
        {"id": "F_title", "name": "Title", "type": "ProjectV2Field"},
        {"id": "F_status", "name": "Status", "type": "ProjectV2SingleSelectField", "options": status},
    ]
    if priority:
        fields.append(
            {"id": "F_prio", "name": "Priority", "type": "ProjectV2SingleSelectField", "options": PRIORITY_OPTIONS}
        )
    return json.dumps({"fields": fields})


class FakeRunner(ghp_common.Runner):
    """Answers commands from tables keyed by argument prefix; records every write."""

    def __init__(self, reads: dict, writes: dict | None = None) -> None:
        super().__init__(dry_run=False)
        self.reads = reads
        self.write_outputs = writes or {}
        self.writes: list[tuple[str, ...]] = []
        self.stdins: list[str | None] = []

    @staticmethod
    def answer(table: dict, args: tuple[str, ...], default: str | None) -> str:
        for prefix, output in table.items():
            if args[: len(prefix)] == prefix:
                return output(args) if callable(output) else output
        if default is None:
            raise AssertionError(f"unexpected read: {args}")
        return default

    def read(self, *args: str, stdin: str | None = None) -> str:
        return self.answer(self.reads, args, default=None)

    def write(self, *args: str, stdin: str | None = None, dry_output: str = "") -> str:
        self.writes.append(args)
        self.stdins.append(stdin)
        return self.answer(self.write_outputs, args, default="")


@pytest.fixture
def repo_dir(tmp_path, monkeypatch):
    (tmp_path / ".gh-pm.yml").write_text(GH_PM_YML)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def milestone_reads(fields: str = field_list(), labels=("bug", "enhancement", "docs", "test", "perf")) -> dict:
    return {
        ("gh", "repo", "view"): json.dumps({"nameWithOwner": "octo/repo", "defaultBranchRef": {"name": "main"}}),
        ("gh", "label", "list"): json.dumps([{"name": name} for name in labels]),
        ("gh", "project", "field-list"): fields,
        ("gh", "api", "repos/octo/repo/milestones/7"): "Eval Rework",
        ("gh", "api", "repos/octo/repo/git/ref/heads/main"): "abc123",
    }


def milestone_writes() -> dict:
    counter = iter(range(101, 200))
    return {
        ("gh", "milestone", "create"): "Creating milestone in octo/repo\n\nhttps://github.com/octo/repo/milestone/7",
        ("gh", "issue", "create"): lambda args: f"https://github.com/octo/repo/issues/{next(counter)}",
    }


def write_plan(tmp_path: Path, issues: str) -> Path:
    plan = tmp_path / "plan.yml"
    plan.write_text(
        "milestone:\n  title: Eval Rework\n  description: ''\nissues:\n"
        + textwrap.indent(textwrap.dedent(issues), "  ")
    )
    return plan


PLAN = """\
- id: 1
  title: Batch eval
  label: enhancement
  status: in_progress
  sub_issues:
    - id: 2
      title: Fitness
      label: testing
      status: todo
    - id: 3
      title: Docs pass
      label: documentation
      status: review
      blocked_by: [2]
- id: 4
  title: Perf probe
  label: performance
  status: todo
  priority: high
"""


# ---------------------------------------------------------------------------
# ghp_common
# ---------------------------------------------------------------------------


class TestResolveLabel:
    def test_exact_match_case_insensitive(self):
        assert ghp_common.resolve_label("Bug", ["bug"]) == "bug"

    def test_synonym_maps_to_the_repo_name(self):
        assert ghp_common.resolve_label("documentation", ["docs"]) == "docs"
        assert ghp_common.resolve_label("docs", ["documentation"]) == "documentation"
        assert ghp_common.resolve_label("testing", ["test"]) == "test"
        assert ghp_common.resolve_label("performance", ["perf"]) == "perf"

    def test_missing_label(self):
        assert ghp_common.resolve_label("research", ["bug", "docs"]) is None


class TestResolveStatus:
    values = {"todo": "Todo", "in_progress": "In Progress", "in_review": "In Review", "done": "Done"}

    def test_gh_pm_key_passes_through(self):
        assert ghp_common.resolve_status("in_progress", self.values) == "in_progress"

    def test_column_key_maps_to_the_repo_option(self):
        assert ghp_common.resolve_status("review", self.values) == "in_review"

    def test_missing_column(self):
        assert ghp_common.resolve_status("backlog", self.values) is None


class TestPlanStatusOptions:
    def test_adds_backlog_first_and_keeps_existing_options_and_ids(self):
        planned = ghp_common.plan_status_options(STATUS_OPTIONS)
        assert [option["name"] for option in planned] == ["Backlog", "Todo", "In Progress", "In Review", "Done"]
        assert "id" not in planned[0]
        assert planned[1:] == STATUS_OPTIONS

    def test_adds_review_before_done(self):
        existing = [STATUS_OPTIONS[0], STATUS_OPTIONS[1], STATUS_OPTIONS[3]]
        planned = ghp_common.plan_status_options(existing)
        assert [option["name"] for option in planned] == ["Backlog", "Todo", "In Progress", "Review", "Done"]

    def test_custom_option_stays_where_it_is(self):
        existing = [
            STATUS_OPTIONS[0],
            {"id": "x", "name": "Blocked", "color": "RED", "description": ""},
            STATUS_OPTIONS[3],
        ]
        planned = ghp_common.plan_status_options(existing)
        assert [option["name"] for option in planned] == ["Backlog", "Todo", "Blocked", "In Progress", "Review", "Done"]

    def test_complete_board_is_unchanged(self):
        board = ghp_common.plan_status_options(STATUS_OPTIONS)
        assert ghp_common.plan_status_options(board) == board


def test_find_gh_pm_config_walks_up(tmp_path):
    (tmp_path / ".gh-pm.yml").write_text(GH_PM_YML)
    nested = tmp_path / ".claude" / "worktrees" / "42-x"
    nested.mkdir(parents=True)
    assert ghp_common.find_gh_pm_config(nested) == tmp_path / ".gh-pm.yml"


# ---------------------------------------------------------------------------
# create-milestone.py
# ---------------------------------------------------------------------------


class TestCreateMilestone:
    def run(self, repo_dir, plan: str, reads: dict | None = None) -> FakeRunner:
        runner = FakeRunner(reads or milestone_reads(), milestone_writes())
        cm.main([str(write_plan(repo_dir, plan))], runner=runner)
        return runner

    def test_names_the_milestone_after_the_assigned_number(self, repo_dir):
        writes = self.run(repo_dir, PLAN).writes
        assert writes[0] == ("gh", "milestone", "create", "--title", "Eval Rework")
        assert writes[1] == ("gh", "milestone", "edit", "7", "--title", "Milestone 7 - Eval Rework")

    def test_milestone_base_comes_from_the_default_branch_tip(self, repo_dir):
        writes = self.run(repo_dir, PLAN).writes
        assert (
            "gh",
            "api",
            "repos/octo/repo/git/refs",
            "-f",
            "ref=refs/heads/m7-eval-rework",
            "-f",
            "sha=abc123",
        ) in writes
        assert not [w for w in writes if w[:2] == ("git", "checkout")]

    def test_each_branch_forks_from_its_parent(self, repo_dir):
        develops = [w for w in self.run(repo_dir, PLAN).writes if w[:3] == ("gh", "issue", "develop")]
        assert develops == [
            ("gh", "issue", "develop", "101", "--base", "m7-eval-rework", "--name", "m7/101-batch-eval"),
            ("gh", "issue", "develop", "102", "--base", "m7/101-batch-eval", "--name", "m7/101/102-fitness"),
            ("gh", "issue", "develop", "103", "--base", "m7/101-batch-eval", "--name", "m7/101/103-docs-pass"),
            ("gh", "issue", "develop", "104", "--base", "m7-eval-rework", "--name", "m7/104-perf-probe"),
        ]

    def test_uses_the_repo_labels_statuses_and_priorities(self, repo_dir):
        writes = self.run(repo_dir, PLAN).writes
        labels = [w[w.index("--label") + 1] for w in writes if w[:3] == ("gh", "issue", "create")]
        assert labels == ["enhancement", "test", "docs", "perf"]
        moves = [w for w in writes if w[:3] == ("gh", "pm", "move")]
        assert ("gh", "pm", "move", "103", "--status", "in_review", "--priority", "medium") in moves
        assert ("gh", "pm", "move", "104", "--status", "todo", "--priority", "high") in moves

    def test_adds_every_issue_to_the_project(self, repo_dir):
        adds = [w for w in self.run(repo_dir, PLAN).writes if w[:3] == ("gh", "project", "item-add")]
        assert [w[-1] for w in adds] == [f"https://github.com/octo/repo/issues/{n}" for n in (101, 102, 103, 104)]

    @pytest.mark.parametrize(
        ("old", "new", "message"),
        [
            ("status: todo\n  priority: high", "status: backlog", "'backlog' is not a Status option"),
            ("label: performance", "label: research", "label 'research' has no match"),
            ("priority: high", "priority: urgent", "'urgent' is not a Priority option"),
        ],
    )
    def test_problems_fail_before_any_write(self, repo_dir, capsys, old, new, message):
        runner = FakeRunner(milestone_reads(), milestone_writes())
        with pytest.raises(SystemExit) as exc:
            cm.main([str(write_plan(repo_dir, PLAN.replace(old, new)))], runner=runner)
        assert message in str(exc.value)
        assert runner.writes == []

    def test_missing_priority_field_fails_before_any_write(self, repo_dir):
        runner = FakeRunner(milestone_reads(fields=field_list(priority=False)), milestone_writes())
        with pytest.raises(SystemExit, match="no Priority field"):
            cm.main([str(write_plan(repo_dir, PLAN))], runner=runner)
        assert runner.writes == []

    def test_board_option_missing_from_gh_pm_yml_asks_for_a_refresh(self, repo_dir):
        (repo_dir / ".gh-pm.yml").write_text(GH_PM_YML.replace("in_review: In Review, ", ""))
        runner = FakeRunner(milestone_reads(), milestone_writes())
        with pytest.raises(SystemExit, match=r"'review' is on the board but \.gh-pm\.yml is stale"):
            cm.main([str(write_plan(repo_dir, PLAN))], runner=runner)

    def test_milestone_read_back_mismatch_stops_before_renaming(self, repo_dir):
        reads = milestone_reads() | {("gh", "api", "repos/octo/repo/milestones/7"): "Someone Else's"}
        runner = FakeRunner(reads, milestone_writes())
        with pytest.raises(SystemExit, match="milestone #7 is"):
            cm.main([str(write_plan(repo_dir, PLAN))], runner=runner)
        assert runner.writes == [("gh", "milestone", "create", "--title", "Eval Rework")]

    @pytest.mark.parametrize(
        ("plan", "message"),
        [
            (PLAN.replace("id: 4", "id: 3"), "duplicate ids: [3]"),
            (PLAN.replace("blocked_by: [2]", "blocked_by: [9]"), "blocked_by unknown ids [9]"),
            (PLAN.replace("  label: enhancement\n", ""), "item 1: missing label"),
        ],
    )
    def test_invalid_plan(self, repo_dir, plan, message):
        with pytest.raises(SystemExit) as exc:
            self.run(repo_dir, plan)
        assert message in str(exc.value)

    def test_dry_run_reads_but_never_writes(self, repo_dir, monkeypatch, capsys):
        reads = milestone_reads()

        def fake_run(args, *, stdin=None):
            return FakeRunner.answer(reads, tuple(args), default=None)

        monkeypatch.setattr(ghp_common, "run", fake_run)
        cm.main([str(write_plan(repo_dir, PLAN)), "--dry-run"])
        out = capsys.readouterr().out
        assert "[dry-run] gh issue develop 1 --base m0-eval-rework --name m0/1-batch-eval" in out
        assert "[dry-run] gh issue develop 2 --base m0/1-batch-eval --name m0/1/2-fitness" in out


# ---------------------------------------------------------------------------
# repo-setup.py
# ---------------------------------------------------------------------------


class TestRepoSetup:
    def test_creates_only_the_labels_with_no_match(self):
        runner = FakeRunner(
            {
                ("gh", "label", "list"): json.dumps(
                    [{"name": n} for n in ["bug", "enhancement", "docs", "test", "perf", "research"]]
                )
            }
        )
        missing = rs.check_labels(runner, {"defaults": {"labels": ["pm-tracked"]}})
        assert missing == ["needs-revision", "pm-tracked"]
        assert [w[3] for w in runner.writes] == ["needs-revision", "pm-tracked"]
        assert all("--force" not in w for w in runner.writes)

    def test_adds_missing_columns_keeping_existing_ids(self):
        existing = [STATUS_OPTIONS[0], STATUS_OPTIONS[1], STATUS_OPTIONS[3]]
        after = [
            {"id": "new1", "name": "Backlog"},
            *({"id": o["id"], "name": o["name"]} for o in existing),
            {"id": "new2", "name": "Review"},
        ]
        runner = FakeRunner(
            {("gh", "api", "graphql"): json.dumps({"data": {"node": {"options": existing}}})},
            {
                ("gh", "api", "graphql"): json.dumps(
                    {"data": {"updateProjectV2Field": {"projectV2Field": {"options": after}}}}
                )
            },
        )
        assert rs.check_status(runner, json.loads(field_list(status=existing))["fields"]) == ["Backlog", "Review"]
        sent = json.loads(runner.stdins[0])["variables"]["options"]
        assert [o["name"] for o in sent] == ["Backlog", "Todo", "In Progress", "Review", "Done"]
        assert [o.get("id") for o in sent] == [None, "s1", "s2", None, "s4"]

    def test_status_update_that_drops_an_id_fails_loudly(self):
        existing = [STATUS_OPTIONS[0], STATUS_OPTIONS[3]]
        after = [{"id": "fresh", "name": "Todo"}, {"id": "s4", "name": "Done"}]
        runner = FakeRunner(
            {("gh", "api", "graphql"): json.dumps({"data": {"node": {"options": existing}}})},
            {
                ("gh", "api", "graphql"): json.dumps(
                    {"data": {"updateProjectV2Field": {"projectV2Field": {"options": after}}}}
                )
            },
        )
        with pytest.raises(SystemExit, match=r"changed the ids of \['Todo'\]"):
            rs.check_status(runner, json.loads(field_list(status=existing))["fields"])

    def test_complete_board_sends_no_update(self):
        board = ghp_common.plan_status_options(STATUS_OPTIONS)
        runner = FakeRunner({("gh", "api", "graphql"): json.dumps({"data": {"node": {"options": board}}})})
        assert rs.check_status(runner, json.loads(field_list(status=board))["fields"]) == []
        assert runner.writes == []

    def test_creates_the_priority_field_when_missing(self):
        runner = FakeRunner({})
        assert rs.check_priority(runner, json.loads(field_list(priority=False))["fields"], "7", "octo") == ["Priority"]
        assert runner.writes == [
            ("gh", "project", "field-create", "7", "--owner", "octo", "--name", "Priority",
             "--data-type", "SINGLE_SELECT", "--single-select-options", "Critical,High,Medium,Low"),
        ]  # fmt: skip

    def test_stale_mappings(self):
        gh_pm = {"fields": {"status": {"values": {"todo": "Todo", "done": "Done"}}, "priority": {"values": {}}}}
        fields = json.loads(field_list(priority=False, status=[STATUS_OPTIONS[0], STATUS_OPTIONS[3]]))["fields"]
        assert rs.stale_mappings(gh_pm, fields) == []
        gh_pm["metadata"] = {"fields": [{"name": "Status", "options": [{"id": "s1", "name": "Todo"}]}]}
        assert rs.stale_mappings(gh_pm, fields) == ["Status: Done"]
