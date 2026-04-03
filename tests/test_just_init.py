"""Tests for just-init.py script."""

from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path

import pytest

# Load the script module despite the hyphenated filename
SCRIPT_PATH = Path(__file__).parent.parent / "skills" / "just-init" / "scripts" / "just-init.py"
spec = importlib.util.spec_from_file_location("just_init", SCRIPT_PATH)
ji = importlib.util.module_from_spec(spec)
sys.modules["just_init"] = ji
spec.loader.exec_module(ji)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def pkg_dir(tmp_path):
    """Create a minimal Python package."""
    pkg = tmp_path / "mypackage"
    pkg.mkdir()
    (pkg / "__init__.py").write_text('"""Old summary.\n\nmypackage/\n├── __init__.py    # Package init and public exports.\n└── utils.py       # Helper functions.\n"""\n')
    (pkg / "utils.py").write_text("def helper():\n    pass\n")
    (pkg / "models.py").write_text("class User:\n    pass\n\nclass Admin:\n    pass\n")
    return pkg


@pytest.fixture
def pkg_with_defs(tmp_path):
    """Create a package with a file that has 3+ public definitions."""
    pkg = tmp_path / "auth"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "tokens.py").write_text(textwrap.dedent("""\
        class Token:
            value: str

        def create_token(user):
            pass

        def validate_token(token):
            pass

        def refresh_token(token):
            pass
    """))
    (pkg / "config.py").write_text("TIMEOUT = 30\n")
    return pkg


@pytest.fixture
def nested_pkg(tmp_path):
    """Create a package with a sub-package."""
    root = tmp_path / "app"
    root.mkdir()
    (root / "__init__.py").write_text("")
    (root / "main.py").write_text("def run(): pass\n")

    sub = root / "core"
    sub.mkdir()
    (sub / "__init__.py").write_text("")
    (sub / "engine.py").write_text("class Engine: pass\n")
    return root


@pytest.fixture
def empty_pkg(tmp_path):
    """Package with only __init__.py."""
    pkg = tmp_path / "empty"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    return pkg


# ---------------------------------------------------------------------------
# analyze_file
# ---------------------------------------------------------------------------

class TestAnalyzeFile:
    def test_extracts_public_defs(self, pkg_with_defs):
        info = ji.analyze_file(pkg_with_defs / "tokens.py")
        names = [d.name for d in info.definitions]
        assert names == ["Token", "create_token", "refresh_token", "validate_token"]

    def test_classes_before_functions(self, pkg_with_defs):
        info = ji.analyze_file(pkg_with_defs / "tokens.py")
        kinds = [d.kind for d in info.definitions]
        assert kinds == ["class", "function", "function", "function"]

    def test_skips_private(self, tmp_path):
        f = tmp_path / "mod.py"
        f.write_text("def public(): pass\ndef _private(): pass\nclass _Hidden: pass\n")
        info = ji.analyze_file(f)
        assert [d.name for d in info.definitions] == ["public"]

    def test_has_line_numbers(self, pkg_with_defs):
        info = ji.analyze_file(pkg_with_defs / "tokens.py")
        token = info.definitions[0]
        assert token.lineno >= 1
        assert token.end_lineno >= token.lineno

    def test_syntax_error_returns_empty(self, tmp_path):
        f = tmp_path / "bad.py"
        f.write_text("def broken(:\n")
        info = ji.analyze_file(f)
        assert info.definitions == []

    def test_async_functions(self, tmp_path):
        f = tmp_path / "async_mod.py"
        f.write_text("async def fetch(): pass\nasync def send(): pass\n")
        info = ji.analyze_file(f)
        assert [d.name for d in info.definitions] == ["fetch", "send"]
        assert all(d.kind == "async_function" for d in info.definitions)


# ---------------------------------------------------------------------------
# parse_existing_docstring
# ---------------------------------------------------------------------------

class TestParseExistingDocstring:
    def test_parses_summary(self, pkg_dir):
        parsed = ji.parse_existing_docstring(pkg_dir / "__init__.py")
        assert parsed.summary == "Old summary."

    def test_parses_entries(self, pkg_dir):
        parsed = ji.parse_existing_docstring(pkg_dir / "__init__.py")
        assert "__init__.py" in parsed.entries
        assert "utils.py" in parsed.entries
        assert parsed.entries["utils.py"].description == "Helper functions."

    def test_parses_package_name(self, pkg_dir):
        parsed = ji.parse_existing_docstring(pkg_dir / "__init__.py")
        assert parsed.package_name == "mypackage"

    def test_no_docstring_returns_none(self, tmp_path):
        f = tmp_path / "__init__.py"
        f.write_text("import os\n")
        assert ji.parse_existing_docstring(f) is None

    def test_missing_file_returns_none(self, tmp_path):
        assert ji.parse_existing_docstring(tmp_path / "nope.py") is None

    def test_empty_file_returns_none(self, tmp_path):
        f = tmp_path / "__init__.py"
        f.write_text("")
        assert ji.parse_existing_docstring(f) is None

    def test_parses_sub_entries(self, tmp_path):
        f = tmp_path / "__init__.py"
        f.write_text(textwrap.dedent('''\
            """
            My package.

            pkg/
            ├── __init__.py    # Package init and public exports.
            ├── tokens.py      # Token handling.
            │   ├── Token           # JWT token. [1:10]
            │   └── create_token    # Create token. [12:20]
            └── utils.py       # Helpers.
            """
        '''))
        parsed = ji.parse_existing_docstring(f)
        assert "tokens.py" in parsed.entries
        entry = parsed.entries["tokens.py"]
        assert len(entry.sub_entries) == 2
        assert entry.sub_entries[0] == ("Token", "JWT token.", "1:10")

    def test_parses_sub_entries_under_last_item(self, tmp_path):
        """Sub-entries under └── use space prefix instead of │."""
        f = tmp_path / "__init__.py"
        f.write_text(textwrap.dedent('''\
            """
            My package.

            pkg/
            ├── __init__.py    # Package init and public exports.
            └── tokens.py      # Token handling.
                ├── Token           # JWT token. [1:10]
                └── create_token    # Create token. [12:20]
            """
        '''))
        parsed = ji.parse_existing_docstring(f)
        entry = parsed.entries["tokens.py"]
        assert len(entry.sub_entries) == 2


# ---------------------------------------------------------------------------
# discover_packages
# ---------------------------------------------------------------------------

class TestDiscoverPackages:
    def test_finds_package(self, pkg_dir):
        packages = ji.discover_packages(pkg_dir, set())
        assert len(packages) == 1
        assert packages[0].path == pkg_dir

    def test_finds_nested(self, nested_pkg):
        packages = ji.discover_packages(nested_pkg, set())
        paths = {p.path for p in packages}
        assert nested_pkg in paths
        assert nested_pkg / "core" in paths

    def test_skips_venv(self, tmp_path):
        pkg = tmp_path / "myapp"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        venv = tmp_path / ".venv"
        venv.mkdir()
        (venv / "__init__.py").write_text("")
        packages = ji.discover_packages(tmp_path, set())
        paths = {p.path for p in packages}
        assert pkg in paths
        assert venv not in paths

    def test_lists_py_files(self, pkg_dir):
        packages = ji.discover_packages(pkg_dir, set())
        names = [f.name for f in packages[0].py_files]
        assert "utils.py" in names
        assert "models.py" in names
        assert "__init__.py" not in names

    def test_lists_subdirs(self, nested_pkg):
        packages = ji.discover_packages(nested_pkg, set())
        root_pkg = [p for p in packages if p.path == nested_pkg][0]
        assert ("core", True) in root_pkg.subdirs


# ---------------------------------------------------------------------------
# render_docstring
# ---------------------------------------------------------------------------

class TestRenderDocstring:
    def test_preserves_old_descriptions(self, pkg_dir):
        packages = ji.discover_packages(pkg_dir, set())
        pkg = packages[0]
        file_infos = {f: ji.analyze_file(f) for f in pkg.py_files}
        old = ji.parse_existing_docstring(pkg.init_path)
        result = ji.render_docstring(pkg, file_infos, old)
        assert "Helper functions." in result

    def test_new_entries_get_todo(self, pkg_dir):
        packages = ji.discover_packages(pkg_dir, set())
        pkg = packages[0]
        file_infos = {f: ji.analyze_file(f) for f in pkg.py_files}
        old = ji.parse_existing_docstring(pkg.init_path)
        result = ji.render_docstring(pkg, file_infos, old)
        assert "models.py" in result
        assert "TODO: describe." in result

    def test_includes_line_index(self, pkg_with_defs):
        packages = ji.discover_packages(pkg_with_defs, set())
        pkg = packages[0]
        file_infos = {f: ji.analyze_file(f) for f in pkg.py_files}
        result = ji.render_docstring(pkg, file_infos, None)
        assert "Token" in result
        assert "create_token" in result
        # Should have line range format
        lines = result.splitlines()
        sub_lines = [l for l in lines if "Token" in l and "#" in l]
        assert any(":" in l.split("#")[1] for l in sub_lines)

    def test_no_line_index_below_threshold(self, pkg_dir):
        """utils.py has only 1 function — no sub-entries."""
        packages = ji.discover_packages(pkg_dir, set())
        pkg = packages[0]
        file_infos = {f: ji.analyze_file(f) for f in pkg.py_files}
        result = ji.render_docstring(pkg, file_infos, None)
        assert "helper" not in result  # function name should NOT appear as sub-entry

    def test_preserves_summary(self, pkg_dir):
        packages = ji.discover_packages(pkg_dir, set())
        pkg = packages[0]
        file_infos = {f: ji.analyze_file(f) for f in pkg.py_files}
        old = ji.parse_existing_docstring(pkg.init_path)
        result = ji.render_docstring(pkg, file_infos, old)
        assert result.startswith("Old summary.")

    def test_init_always_first(self, pkg_with_defs):
        packages = ji.discover_packages(pkg_with_defs, set())
        pkg = packages[0]
        file_infos = {f: ji.analyze_file(f) for f in pkg.py_files}
        result = ji.render_docstring(pkg, file_infos, None)
        lines = [l for l in result.splitlines() if "──" in l]
        assert "__init__.py" in lines[0]


# ---------------------------------------------------------------------------
# write_docstring
# ---------------------------------------------------------------------------

class TestWriteDocstring:
    def test_creates_new_file(self, tmp_path):
        init = tmp_path / "__init__.py"
        assert ji.write_docstring(init, "My package.\n\npkg/\n└── __init__.py    # Init.")
        assert init.exists()
        assert '"""' in init.read_text()

    def test_replaces_existing_docstring(self, pkg_dir):
        old_content = (pkg_dir / "__init__.py").read_text()
        assert "Old summary." in old_content
        ji.write_docstring(pkg_dir / "__init__.py", "New summary.\n\nmypackage/\n└── __init__.py    # Init.")
        new_content = (pkg_dir / "__init__.py").read_text()
        assert "New summary." in new_content
        assert "Old summary." not in new_content

    def test_preserves_code_after_docstring(self, tmp_path):
        init = tmp_path / "__init__.py"
        init.write_text('"""Old.\n"""\n\nimport os\nVAR = 1\n')
        ji.write_docstring(init, "New.")
        content = init.read_text()
        assert "import os" in content
        assert "VAR = 1" in content
        assert "New." in content

    def test_returns_false_when_unchanged(self, tmp_path):
        init = tmp_path / "__init__.py"
        docstring = "My package.\n\npkg/\n└── __init__.py    # Init."
        ji.write_docstring(init, docstring)
        assert not ji.write_docstring(init, docstring)

    def test_prepends_to_file_without_docstring(self, tmp_path):
        init = tmp_path / "__init__.py"
        init.write_text("import os\n")
        ji.write_docstring(init, "My package.")
        content = init.read_text()
        assert content.startswith('"""')
        assert "import os" in content


# ---------------------------------------------------------------------------
# verify_package
# ---------------------------------------------------------------------------

class TestVerifyPackage:
    def test_clean_package(self, pkg_dir):
        """After generate, verify should find no issues."""
        packages = ji.discover_packages(pkg_dir, set())
        pkg = packages[0]
        file_infos = {f: ji.analyze_file(f) for f in pkg.py_files}
        old = ji.parse_existing_docstring(pkg.init_path)
        new_doc = ji.render_docstring(pkg, file_infos, old)
        ji.write_docstring(pkg.init_path, new_doc)

        parsed = ji.parse_existing_docstring(pkg.init_path)
        issues = ji.verify_package(pkg, file_infos, parsed)
        assert issues == []

    def test_detects_missing_entry(self, pkg_dir):
        """Old docstring doesn't list models.py."""
        packages = ji.discover_packages(pkg_dir, set())
        pkg = packages[0]
        file_infos = {f: ji.analyze_file(f) for f in pkg.py_files}
        parsed = ji.parse_existing_docstring(pkg.init_path)
        issues = ji.verify_package(pkg, file_infos, parsed)
        assert any("models.py" in i for i in issues)

    def test_detects_extra_entry(self, tmp_path):
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text('"""Summary.\n\npkg/\n├── __init__.py    # Init.\n└── ghost.py       # Gone.\n"""\n')
        packages = ji.discover_packages(pkg, set())
        p = packages[0]
        file_infos = {f: ji.analyze_file(f) for f in p.py_files}
        parsed = ji.parse_existing_docstring(p.init_path)
        issues = ji.verify_package(p, file_infos, parsed)
        assert any("ghost.py" in i for i in issues)

    def test_detects_missing_docstring(self, empty_pkg):
        packages = ji.discover_packages(empty_pkg, set())
        pkg = packages[0]
        parsed = ji.parse_existing_docstring(pkg.init_path)
        issues = ji.verify_package(pkg, {}, parsed)
        assert any("missing docstring" in i for i in issues)


# ---------------------------------------------------------------------------
# Integration: generate → verify → update cycle
# ---------------------------------------------------------------------------

class TestIntegration:
    def test_generate_then_verify_clean(self, pkg_with_defs):
        assert ji.cmd_generate(pkg_with_defs, verbose=False) == 0
        assert ji.cmd_verify(pkg_with_defs, verbose=False) == 0

    def test_generate_idempotent(self, pkg_with_defs):
        ji.cmd_generate(pkg_with_defs, verbose=False)
        content_after_first = (pkg_with_defs / "__init__.py").read_text()
        ji.cmd_generate(pkg_with_defs, verbose=False)
        content_after_second = (pkg_with_defs / "__init__.py").read_text()
        assert content_after_first == content_after_second

    def test_update_fixes_stale(self, pkg_with_defs):
        ji.cmd_generate(pkg_with_defs, verbose=False)
        # Add a new file
        (pkg_with_defs / "middleware.py").write_text("def check_auth(): pass\n")
        # Verify should fail
        assert ji.cmd_verify(pkg_with_defs, verbose=False) == 1
        # Update should fix
        assert ji.cmd_update(pkg_with_defs, verbose=False) == 0
        # Verify should pass
        assert ji.cmd_verify(pkg_with_defs, verbose=False) == 0

    def test_nested_packages(self, nested_pkg):
        ji.cmd_generate(nested_pkg, verbose=False)
        assert ji.cmd_verify(nested_pkg, verbose=False) == 0
        # Both __init__.py files should have docstrings
        root_doc = ji.parse_existing_docstring(nested_pkg / "__init__.py")
        sub_doc = ji.parse_existing_docstring(nested_pkg / "core" / "__init__.py")
        assert root_doc is not None
        assert sub_doc is not None
        assert "core/" in root_doc.entries

    def test_description_preserved_across_updates(self, pkg_dir):
        """Existing descriptions survive generate cycles."""
        ji.cmd_generate(pkg_dir, verbose=False)
        parsed = ji.parse_existing_docstring(pkg_dir / "__init__.py")
        assert parsed.entries["utils.py"].description == "Helper functions."
        # Add a file and regenerate
        (pkg_dir / "new.py").write_text("pass\n")
        ji.cmd_generate(pkg_dir, verbose=False)
        parsed2 = ji.parse_existing_docstring(pkg_dir / "__init__.py")
        assert parsed2.entries["utils.py"].description == "Helper functions."
