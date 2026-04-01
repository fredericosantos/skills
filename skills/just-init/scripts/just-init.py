#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
"""Manage __init__.py docstrings as living package indexes."""

from __future__ import annotations

import argparse
import ast
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePath

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SKIP_DIRS: frozenset[str] = frozenset({
    "site-packages", ".venv", "venv", "env", "__pycache__",
    ".git", ".hg", ".svn", "node_modules", ".tox",
    ".mypy_cache", ".pytest_cache", ".ruff_cache",
    "vendor", "vendored", "third_party",
    ".eggs", "build", "dist",
})

LINE_INDEX_THRESHOLD = 3  # files with 3+ public defs get sub-entries

INIT_DESCRIPTION = "Package init and public exports."

# Regex patterns for parsing existing docstrings
# Main entry: "├── name  # description" or "├── name  # description [1:15]"
ENTRY_RE = re.compile(r"^[├└]── (\S+)\s+# (.+?)(?:\s+\[(\d+):(\d+)\])?\s*$")
# Sub-entry: "│   ├── name  # description [10:50]" or "    ├── name  # description [10:50]"
SUBENTRY_RE = re.compile(r"^(?:│\s+|\s{2,})[├└]── (\S+)\s+# (.+?)(?:\s+\[(\d+):(\d+)\])?\s*$")
PACKAGE_HEADER_RE = re.compile(r"^(\w[\w.-]*)/\s*$")

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Definition:
    name: str
    kind: str  # "class" | "function" | "async_function"
    lineno: int
    end_lineno: int
    description: str = "TODO: describe."


@dataclass
class FileInfo:
    path: Path
    definitions: list[Definition] = field(default_factory=list)


@dataclass
class ParsedEntry:
    name: str
    description: str
    line_range: tuple[int, int] | None = None  # [start:end] if present
    sub_entries: list[tuple[str, str, str]] = field(default_factory=list)  # (name, desc, "start:end")


@dataclass
class ParsedDocstring:
    summary: str
    package_name: str
    entries: dict[str, ParsedEntry] = field(default_factory=dict)


@dataclass
class PackageInfo:
    path: Path
    init_path: Path
    py_files: list[Path] = field(default_factory=list)
    subdirs: list[tuple[str, bool]] = field(default_factory=list)  # (name, is_python_package)
    docstring_range: tuple[int, int] | None = None  # (start_line, end_line) of docstring

# ---------------------------------------------------------------------------
# Section 1: Gitignore loading
# ---------------------------------------------------------------------------

def load_gitignore_patterns(root: Path) -> set[str]:
    """Parse .gitignore at root and return a set of patterns."""
    gitignore = root / ".gitignore"
    if not gitignore.is_file():
        return set()
    patterns: set[str] = set()
    for line in gitignore.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.add(line.rstrip("/"))
    return patterns


def should_skip(dirname: str, gitignore_patterns: set[str]) -> bool:
    """Check if a directory name should be skipped."""
    if dirname in SKIP_DIRS:
        return True
    pure = PurePath(dirname)
    return any(pure.match(pat) for pat in gitignore_patterns)

# ---------------------------------------------------------------------------
# Section 2: AST analysis
# ---------------------------------------------------------------------------

def analyze_file(path: Path) -> FileInfo:
    """Extract public top-level definitions from a Python file."""
    info = FileInfo(path=path)
    try:
        source = path.read_text(errors="replace")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, ValueError) as e:
        print(f"  warning: could not parse {path}: {e}", file=sys.stderr)
        return info

    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            doc = ast.get_docstring(node)
            desc = doc.split("\n")[0].rstrip(".") + "." if doc else "TODO: describe."
            info.definitions.append(Definition(
                name=node.name, kind="class",
                lineno=node.lineno, end_lineno=node.end_lineno or node.lineno,
                description=desc,
            ))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            kind = "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"
            doc = ast.get_docstring(node)
            desc = doc.split("\n")[0].rstrip(".") + "." if doc else "TODO: describe."
            info.definitions.append(Definition(
                name=node.name, kind=kind,
                lineno=node.lineno, end_lineno=node.end_lineno or node.lineno,
                description=desc,
            ))

    # Sort: classes first (alpha), then functions (alpha)
    info.definitions.sort(key=lambda d: (0 if d.kind == "class" else 1, d.name))
    return info

# ---------------------------------------------------------------------------
# Section 3: Docstring parsing
# ---------------------------------------------------------------------------

def parse_existing_docstring(init_path: Path) -> ParsedDocstring | None:
    """Parse an existing __init__.py docstring into structured data."""
    if not init_path.is_file():
        return None

    try:
        source = init_path.read_text(errors="replace")
        tree = ast.parse(source, filename=str(init_path))
    except (SyntaxError, ValueError):
        return None

    # Check for module-level docstring
    if not tree.body:
        return None
    first = tree.body[0]
    if not isinstance(first, ast.Expr) or not isinstance(first.value, ast.Constant):
        return None
    if not isinstance(first.value.value, str):
        return None

    docstring = first.value.value
    lines = docstring.strip().splitlines()
    if not lines:
        return None

    summary = lines[0].strip()
    package_name = ""
    entries: dict[str, ParsedEntry] = {}
    current_entry: ParsedEntry | None = None

    for line in lines[1:]:
        stripped = line.strip()
        if not stripped:
            continue

        # Check for package header
        header_match = PACKAGE_HEADER_RE.match(stripped)
        if header_match:
            package_name = header_match.group(1)
            continue

        # Check for sub-entry (must check before main entry)
        sub_match = SUBENTRY_RE.match(line)
        if sub_match and current_entry is not None:
            sub_name = sub_match.group(1)
            sub_desc = sub_match.group(2)
            sub_range = f"{sub_match.group(3)}:{sub_match.group(4)}" if sub_match.group(3) else ""
            current_entry.sub_entries.append((sub_name, sub_desc, sub_range))
            continue

        # Check for main entry
        entry_match = ENTRY_RE.match(line)
        if entry_match:
            name = entry_match.group(1)
            desc = entry_match.group(2)
            lr = (int(entry_match.group(3)), int(entry_match.group(4))) if entry_match.group(3) else None
            current_entry = ParsedEntry(name=name, description=desc, line_range=lr)
            entries[name] = current_entry

    return ParsedDocstring(summary=summary, package_name=package_name, entries=entries)

# ---------------------------------------------------------------------------
# Section 4: Package discovery
# ---------------------------------------------------------------------------

def discover_packages(root: Path, gitignore_patterns: set[str]) -> list[PackageInfo]:
    """Walk root and discover all Python packages."""
    packages: list[PackageInfo] = []

    for dirpath, dirnames, filenames in os.walk(root, topdown=True):
        # Prune skipped directories in-place
        dirnames[:] = sorted(
            d for d in dirnames if not should_skip(d, gitignore_patterns)
        )

        current = Path(dirpath)
        init_path = current / "__init__.py"

        # Only process directories that are Python packages (have __init__.py)
        if not init_path.exists():
            continue

        py_files = sorted(
            current / f for f in filenames
            if f.endswith(".py") and f != "__init__.py"
        )

        subdirs: list[tuple[str, bool]] = []
        for d in sorted(dirnames):
            is_pkg = (current / d / "__init__.py").exists()
            subdirs.append((d, is_pkg))

        packages.append(PackageInfo(
            path=current,
            init_path=init_path,
            py_files=py_files,
            subdirs=subdirs,
        ))

    return packages

# ---------------------------------------------------------------------------
# Section 5: Tree rendering
# ---------------------------------------------------------------------------

def get_docstring_range(init_path: Path) -> tuple[int, int] | None:
    """Get the line range of the docstring in an __init__.py file."""
    if not init_path.is_file():
        return None
    try:
        source = init_path.read_text(errors="replace")
        tree = ast.parse(source, filename=str(init_path))
    except (SyntaxError, ValueError) as e:
        print(f"  warning: cannot read docstring range from {init_path}: {e}", file=sys.stderr)
        return None
    if not tree.body:
        return None
    first = tree.body[0]
    if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)):
        return (first.lineno, first.end_lineno)
    return None


def render_docstring(
    pkg: PackageInfo,
    file_infos: dict[Path, FileInfo],
    old_parsed: ParsedDocstring | None,
    sub_docstring_ranges: dict[str, tuple[int, int]] | None = None,
    sub_summaries: dict[str, str] | None = None,
) -> str:
    """Build the docstring text for a package."""
    pkg_name = pkg.path.name
    sub_ranges = sub_docstring_ranges or {}
    summaries = sub_summaries or {}

    # Summary
    if old_parsed and old_parsed.summary and old_parsed.summary != "TODO: describe this package.":
        summary = old_parsed.summary
    else:
        summary = "TODO: describe this package."

    # Build entry list: __init__.py first, then subdirs (alpha), then .py files (alpha)
    entry_names: list[str] = ["__init__.py"]
    entry_names.extend(f"{name}/" for name, _ in pkg.subdirs)
    entry_names.extend(f.name for f in pkg.py_files)

    total = len(entry_names)

    # Calculate column alignment
    max_name_len = max((len(n) for n in entry_names), default=0)
    col = max_name_len + 8  # "├── " (4) + name + padding to "#"

    lines: list[str] = [summary, "", f"{pkg_name}/"]

    for i, name in enumerate(entry_names):
        is_last_entry = (i == total - 1)
        connector = "└──" if is_last_entry else "├──"

        # Get description
        dir_base = name.rstrip("/")
        if name == "__init__.py":
            desc = INIT_DESCRIPTION
        elif old_parsed and name in old_parsed.entries:
            desc = old_parsed.entries[name].description
        elif name.endswith("/") and dir_base in summaries:
            desc = summaries[dir_base]
        else:
            desc = "TODO: describe."

        padded = f"{connector} {name}".ljust(col)

        # Add [start:end] for subdirectories (their __init__.py docstring range)
        if name.endswith("/") and dir_base in sub_ranges:
            s, e = sub_ranges[dir_base]
            lines.append(f"{padded}# {desc} [{s}:{e}]")
        else:
            lines.append(f"{padded}# {desc}")

        # Add line index sub-entries if applicable
        if name.endswith(".py") and name != "__init__.py":
            file_path = pkg.path / name
            file_info = file_infos.get(file_path)
            if file_info and len(file_info.definitions) >= LINE_INDEX_THRESHOLD:
                sub_prefix = "│" if not is_last_entry else " "
                defs = file_info.definitions
                max_def_name = max((len(d.name) for d in defs), default=0)
                sub_col = max_def_name + 8

                for j, defn in enumerate(defs):
                    is_last_sub = (j == len(defs) - 1)
                    sub_conn = "└──" if is_last_sub else "├──"
                    sub_padded = f"{sub_conn} {defn.name}".ljust(sub_col)
                    lines.append(f"{sub_prefix}   {sub_padded}# {defn.description} [{defn.lineno}:{defn.end_lineno}]")

    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Section 6: Docstring writing
# ---------------------------------------------------------------------------

def write_docstring(init_path: Path, new_docstring: str) -> bool:
    """Write or update the docstring in an __init__.py file. Returns True if modified."""
    formatted = f'"""\n{new_docstring}\n"""\n'

    if not init_path.exists():
        init_path.write_text(formatted)
        return True

    source = init_path.read_text(errors="replace")
    file_lines = source.splitlines(keepends=True)

    try:
        tree = ast.parse(source, filename=str(init_path))
    except (SyntaxError, ValueError) as e:
        # Can't parse — refuse to write to avoid duplicating content
        print(f"  warning: cannot update {init_path} (syntax error: {e})", file=sys.stderr)
        return False

    # Check if module-level docstring exists
    if (tree.body
        and isinstance(tree.body[0], ast.Expr)
        and isinstance(tree.body[0].value, ast.Constant)
        and isinstance(tree.body[0].value.value, str)):

        node = tree.body[0]
        start = node.lineno - 1  # 0-indexed
        end = node.end_lineno  # exclusive (end_lineno is 1-indexed, so this works)

        # Check if content would be the same
        old_block = "".join(file_lines[start:end])
        if old_block.rstrip() == formatted.rstrip():
            return False

        new_lines = file_lines[:start] + [formatted] + file_lines[end:]
        init_path.write_text("".join(new_lines))
        return True
    else:
        # No existing docstring — prepend
        init_path.write_text(formatted + "\n" + source)
        return True

# ---------------------------------------------------------------------------
# Section 7: Verification
# ---------------------------------------------------------------------------

def verify_package(
    pkg: PackageInfo,
    file_infos: dict[Path, FileInfo],
    parsed: ParsedDocstring | None,
) -> list[str]:
    """Verify a package's docstring matches reality. Returns list of issues."""
    issues: list[str] = []
    rel = pkg.init_path

    if parsed is None:
        issues.append(f"STALE: {rel} — missing docstring")
        return issues

    # Expected entries
    expected: set[str] = {"__init__.py"}
    expected.update(f.name for f in pkg.py_files)
    expected.update(f"{name}/" for name, _ in pkg.subdirs)

    documented = set(parsed.entries.keys())

    # Missing from docstring
    for name in sorted(expected - documented):
        issues.append(f"STALE: {rel} — missing entry: {name}")

    # Extra in docstring
    for name in sorted(documented - expected):
        issues.append(f"STALE: {rel} — extra entry: {name}")

    # Stale line indexes
    for py_file in pkg.py_files:
        file_info = file_infos.get(py_file)
        if not file_info or len(file_info.definitions) < LINE_INDEX_THRESHOLD:
            continue

        entry = parsed.entries.get(py_file.name)
        if not entry:
            continue

        # Compare sub-entries (name, description, line_range)
        expected_subs = [(d.name, d.description, f"{d.lineno}:{d.end_lineno}") for d in file_info.definitions]
        if entry.sub_entries != expected_subs:
            issues.append(f"STALE: {rel} — stale line index for {py_file.name}")

    return issues

# ---------------------------------------------------------------------------
# Section 8: CLI and mode dispatch
# ---------------------------------------------------------------------------

def cmd_generate(root: Path, verbose: bool) -> int:
    """Generate/update all __init__.py docstrings under root."""
    gitignore = load_gitignore_patterns(root)
    packages = discover_packages(root, gitignore)

    # Process bottom-up: deepest packages first so parents know child docstring ranges
    packages.sort(key=lambda p: -str(p.path).count(os.sep))

    # Populated as we process children (bottom-up)
    docstring_ranges: dict[Path, tuple[int, int]] = {}
    child_summaries: dict[Path, str] = {}

    created = 0
    updated = 0

    for pkg in packages:
        # Analyze all .py files
        file_infos: dict[Path, FileInfo] = {}
        for py_file in pkg.py_files:
            file_infos[py_file] = analyze_file(py_file)

        # Parse existing docstring
        old_parsed = parse_existing_docstring(pkg.init_path)

        # Collect sub-package info for this package's subdirs
        sub_ranges: dict[str, tuple[int, int]] = {}
        sub_sums: dict[str, str] = {}
        for dir_name, _is_pkg in pkg.subdirs:
            child_path = pkg.path / dir_name
            if child_path in docstring_ranges:
                sub_ranges[dir_name] = docstring_ranges[child_path]
            if child_path in child_summaries:
                sub_sums[dir_name] = child_summaries[child_path]

        # Render new docstring
        new_docstring = render_docstring(pkg, file_infos, old_parsed, sub_ranges, sub_sums)

        # Write
        existed = pkg.init_path.exists()
        if write_docstring(pkg.init_path, new_docstring):
            if existed:
                updated += 1
                if verbose:
                    print(f"  updated: {pkg.init_path}")
            else:
                created += 1
                if verbose:
                    print(f"  created: {pkg.init_path}")

        # Record this package's info for its parent
        dr = get_docstring_range(pkg.init_path)
        if dr:
            docstring_ranges[pkg.path] = dr
        parsed_after = parse_existing_docstring(pkg.init_path)
        if parsed_after and parsed_after.summary and parsed_after.summary != "TODO: describe this package.":
            child_summaries[pkg.path] = parsed_after.summary

    print(f"{len(packages)} packages processed, {created} created, {updated} updated")
    return 0


def cmd_verify(root: Path, verbose: bool) -> int:
    """Verify all __init__.py docstrings match reality."""
    gitignore = load_gitignore_patterns(root)
    packages = discover_packages(root, gitignore)

    all_issues: list[str] = []

    for pkg in packages:
        file_infos: dict[Path, FileInfo] = {}
        for py_file in pkg.py_files:
            file_infos[py_file] = analyze_file(py_file)

        parsed = parse_existing_docstring(pkg.init_path)
        issues = verify_package(pkg, file_infos, parsed)
        all_issues.extend(issues)

    if all_issues:
        for issue in all_issues:
            print(issue)
        print(f"\n{len(all_issues)} issue(s) found")
        return 1

    if verbose:
        print(f"{len(packages)} packages verified, all clean")
    return 0


def cmd_update(root: Path, verbose: bool) -> int:
    """Update only stale __init__.py docstrings."""
    gitignore = load_gitignore_patterns(root)
    packages = discover_packages(root, gitignore)

    # Bottom-up for docstring range and summary propagation
    packages.sort(key=lambda p: -str(p.path).count(os.sep))
    docstring_ranges: dict[Path, tuple[int, int]] = {}
    child_summaries: dict[Path, str] = {}

    fixed = 0

    for pkg in packages:
        file_infos: dict[Path, FileInfo] = {}
        for py_file in pkg.py_files:
            file_infos[py_file] = analyze_file(py_file)

        parsed = parse_existing_docstring(pkg.init_path)
        issues = verify_package(pkg, file_infos, parsed)

        if issues:
            sub_ranges: dict[str, tuple[int, int]] = {}
            sub_sums: dict[str, str] = {}
            for dir_name, _is_pkg in pkg.subdirs:
                child_path = pkg.path / dir_name
                if child_path in docstring_ranges:
                    sub_ranges[dir_name] = docstring_ranges[child_path]
                if child_path in child_summaries:
                    sub_sums[dir_name] = child_summaries[child_path]

            new_docstring = render_docstring(pkg, file_infos, parsed, sub_ranges, sub_sums)
            if write_docstring(pkg.init_path, new_docstring):
                fixed += 1
                if verbose:
                    print(f"  fixed: {pkg.init_path}")
                    for issue in issues:
                        print(f"    {issue}")

        # Record info for parent
        dr = get_docstring_range(pkg.init_path)
        if dr:
            docstring_ranges[pkg.path] = dr
        parsed_after = parse_existing_docstring(pkg.init_path)
        if parsed_after and parsed_after.summary and parsed_after.summary != "TODO: describe this package.":
            child_summaries[pkg.path] = parsed_after.summary

    print(f"{fixed} package(s) updated")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="just-init",
        description="Manage __init__.py docstrings as living package indexes.",
    )
    parser.add_argument("mode", choices=["generate", "verify", "update"])
    parser.add_argument("path", type=Path, help="Root directory to manage")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    root = args.path.resolve()
    if not root.is_dir():
        print(f"Error: {root} is not a directory", file=sys.stderr)
        return 1

    match args.mode:
        case "generate":
            return cmd_generate(root, args.verbose)
        case "verify":
            return cmd_verify(root, args.verbose)
        case "update":
            return cmd_update(root, args.verbose)

    return 0


if __name__ == "__main__":
    sys.exit(main())
