"""Create a milestone with issues, sub-issues, branches, and project tracking.

Reads a YAML plan file and executes all GitHub CLI commands in the right order.

Usage:
    python skills/ghp/scripts/create-milestone.py <plan.yml>
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml


def run(cmd: str, *, check: bool = True) -> str:
    """Run a shell command and return stdout."""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"ERROR: {cmd}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def extract_issue_number(output: str) -> int:
    """Extract issue number from gh issue create output URL."""
    match = re.search(r"/issues/(\d+)", output)
    if not match:
        match = re.search(r"(\d+)\s*$", output)
    if not match:
        print(f"ERROR: Could not extract issue number from: {output}", file=sys.stderr)
        sys.exit(1)
    return int(match.group(1))


def slugify(text: str) -> str:
    """Convert text to a branch-name-safe slug."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def create_issue(title: str, label: str, milestone: str, body: str) -> int:
    """Create a GitHub issue and return its number."""
    body_escaped = body.replace("'", "'\\''")
    cmd = (
        f"gh issue create --title '{title}' --label '{label}' "
        f"--milestone '{milestone}' --body '{body_escaped}'"
    )
    output = run(cmd)
    number = extract_issue_number(output)
    print(f"  Created #{number}: {title}")
    return number


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python create-milestone.py <plan.yml>")
        sys.exit(1)

    plan_path = Path(sys.argv[1])
    if not plan_path.exists():
        print(f"ERROR: {plan_path} not found")
        sys.exit(1)

    plan = yaml.safe_load(plan_path.read_text())
    milestone_cfg = plan["milestone"]
    issues_cfg = plan.get("issues", [])

    # --- Step 1: Create milestone ---
    milestone_title_input = milestone_cfg["title"]
    description = milestone_cfg.get("description", "")

    desc_flag = f" --description '{description}'" if description else ""
    output = run(f"gh milestone create --title '{milestone_title_input}'{desc_flag}")

    # Extract milestone number from URL
    milestone_match = re.search(r"/milestone/(\d+)", output)
    if not milestone_match:
        print(f"ERROR: Could not extract milestone number from: {output}", file=sys.stderr)
        sys.exit(1)
    milestone_number = int(milestone_match.group(1))
    milestone_name = f"Milestone {milestone_number} - {milestone_title_input}"

    # Rename milestone to include the number prefix
    run(f"gh milestone edit {milestone_number} --title '{milestone_name}'")

    print(f"Created milestone: {milestone_name}")

    # --- Step 2: Create milestone branch ---
    branch_slug = plan.get("branch") or f"m{milestone_number}-{slugify(milestone_title_input)}"
    run(f"git checkout -b {branch_slug}")
    run(f"git push -u origin {branch_slug}")
    print(f"Created branch: {branch_slug}")

    # --- Step 3: Create all issues and build ID map ---
    id_map: dict[int, int] = {}  # local_id -> github_number
    issue_meta: dict[int, dict] = {}  # local_id -> {slug, parent_local_id}

    for issue in issues_cfg:
        local_id = issue["id"]
        number = create_issue(
            title=issue["title"],
            label=issue["label"],
            milestone=milestone_name,
            body=issue.get("body", ""),
        )
        id_map[local_id] = number
        issue_meta[local_id] = {
            "slug": slugify(issue["title"]),
            "parent_local_id": None,
        }

        # Create sub-issues
        for sub in issue.get("sub_issues", []):
            sub_local_id = sub["id"]
            sub_number = create_issue(
                title=sub["title"],
                label=sub["label"],
                milestone=milestone_name,
                body=sub.get("body", ""),
            )
            id_map[sub_local_id] = sub_number
            issue_meta[sub_local_id] = {
                "slug": slugify(sub["title"]),
                "parent_local_id": local_id,
            }

    # --- Step 4: Link sub-issues ---
    print("\nLinking sub-issues...")
    for issue in issues_cfg:
        parent_gh = id_map[issue["id"]]
        for sub in issue.get("sub_issues", []):
            child_gh = id_map[sub["id"]]
            run(f"gh issue-ext sub add {parent_gh} {child_gh}")
            print(f"  #{child_gh} is sub-issue of #{parent_gh}")

    # --- Step 5: Set blocking relationships ---
    print("\nSetting blocking relationships...")
    all_items = []
    for issue in issues_cfg:
        all_items.append(issue)
        all_items.extend(issue.get("sub_issues", []))

    has_blocking = False
    for item in all_items:
        for blocker_local_id in item.get("blocked_by", []):
            blocked_gh = id_map[item["id"]]
            blocker_gh = id_map[blocker_local_id]
            run(f"gh issue-ext blocking add {blocked_gh} {blocker_gh}")
            print(f"  #{blocked_gh} is blocked by #{blocker_gh}")
            has_blocking = True
    if not has_blocking:
        print("  (none)")

    # --- Step 6: Create linked branches ---
    # Branch naming: m{N}/{issue}-{slug}, m{N}/{issue}/{sub}-{slug}
    # Uses m{N}/ prefix (not full milestone branch name) to avoid git ref conflicts
    issue_branch_prefix = f"m{milestone_number}"

    print("\nCreating linked branches...")
    for local_id, gh_number in id_map.items():
        meta = issue_meta[local_id]
        slug = meta["slug"]
        parent_local = meta["parent_local_id"]

        if parent_local is None:
            # Top-level issue: m5/34-improve-init-flow
            branch_name = f"{issue_branch_prefix}/{gh_number}-{slug}"
        else:
            # Sub-issue: m5/34/{35}-stale-detection
            parent_gh = id_map[parent_local]
            branch_name = f"{issue_branch_prefix}/{parent_gh}/{gh_number}-{slug}"

        run(f"gh issue-ext branch create {gh_number} --name {branch_name}")
        print(f"  #{gh_number} -> {branch_name}")

    # --- Step 7: Set project status ---
    print("\nSetting project status...")
    for item in all_items:
        status = item.get("status", "todo")
        gh_number = id_map[item["id"]]
        run(f"gh pm move {gh_number} --status {status}", check=False)
        print(f"  #{gh_number} -> {status}")

    # --- Summary ---
    print(f"\nDone! Milestone: {milestone_name} (#{milestone_number})")
    print(f"Branch: {branch_slug}")
    print(f"Issues created: {len(id_map)}")
    print("ID mapping (local -> GitHub):")
    for local_id, gh_number in sorted(id_map.items()):
        print(f"  {local_id} -> #{gh_number}")


if __name__ == "__main__":
    main()
