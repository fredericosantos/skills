"""Checks that the ghp skill files agree with each other and with the scripts."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

GHP = Path(__file__).parent.parent / "skills" / "ghp"
sys.path.insert(0, str(GHP / "scripts"))

import ghp_common  # noqa: E402

SKILL_FILES = sorted(GHP.rglob("SKILL.md"))


def test_label_table_matches_the_label_roles():
    text = (GHP / "SKILL.md").read_text()
    for role in ghp_common.LABEL_ROLES:
        row = next((line for line in text.splitlines() if line.startswith(f"| `{role.name}`")), None)
        assert row is not None, f"no Labels row for {role.name}"
        for synonym in role.synonyms[1:]:
            assert f"`{synonym}`" in row, f"{role.name} row lacks synonym {synonym}"


def test_command_list_matches_the_command_files():
    listed = set(re.findall(r"^- `/ghp:([a-z-]+)`", (GHP / "SKILL.md").read_text(), flags=re.MULTILINE))
    present = {path.parent.name for path in (GHP / "commands").glob("*/SKILL.md")}
    assert listed == present


@pytest.mark.parametrize("path", SKILL_FILES, ids=lambda p: str(p.relative_to(GHP)))
def test_skill_files_use_native_linked_branches(path):
    uses = [
        line
        for line in path.read_text().splitlines()
        if "issue-ext branch" in line and not line.startswith("Don't use")
    ]
    assert uses == []


@pytest.mark.parametrize("path", SKILL_FILES, ids=lambda p: str(p.relative_to(GHP)))
def test_skill_files_reference_files_that_exist(path):
    for relative in re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/(\S+?\.(?:py|yml))", path.read_text()):
        assert (GHP / relative).is_file(), f"{path.name} references missing {relative}"
