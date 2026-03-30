#!/usr/bin/env bash
set -euo pipefail

# Discover unorganized issues and apply status changes to a GitHub Project.
#
# Usage:
#   organize.sh scan   [--repo OWNER/REPO] [--project NUMBER]
#   organize.sh apply  [--repo OWNER/REPO] [--project NUMBER] --choices '{"42":"Todo","43":"In Progress"}'
#
# scan:  Finds open issues not in the Project or missing a status.
# apply: Adds items to Project and sets status. Values: "Todo", "In Progress", "Done", "Skip"

REPO=""
PROJECT=""
CHOICES=""
ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo) REPO="$2"; shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --choices) CHOICES="$2"; shift 2 ;;
    *) ARGS+=("$1"); shift ;;
  esac
done
set -- "${ARGS[@]:-}"

# Auto-detect repo
if [[ -z "$REPO" ]]; then
  REPO=$(git remote get-url origin 2>/dev/null | sed -E 's#.+github\.com[:/]([^/]+/[^/.]+)(\.git)?$#\1#')
fi
if [[ -z "$REPO" ]]; then
  echo "Error: Could not detect repo. Use --repo owner/repo" >&2; exit 1
fi
OWNER="${REPO%%/*}"

# Auto-detect project linked to this repo
if [[ -z "$PROJECT" ]]; then
  REPO_SHORT="${REPO##*/}"
  ALL_PROJECTS=$(gh project list --owner "$OWNER" --format json -q '.projects[].number')
  while read -r PROJ_NUM; do
    [[ -z "$PROJ_NUM" ]] && continue
    HAS_REPO=$(gh project item-list "$PROJ_NUM" --owner "$OWNER" --format json \
      -q "[.items[] | select(.content.repository | endswith(\"${REPO_SHORT}\"))] | length")
    if [[ "$HAS_REPO" -gt 0 ]]; then
      PROJECT="$PROJ_NUM"
      break
    fi
  done <<< "$ALL_PROJECTS"
fi
if [[ -z "$PROJECT" ]]; then
  echo "No project linked. Creating project \"${REPO_SHORT}\"..." >&2
  PROJECT=$(gh project create --owner "$OWNER" --title "$REPO_SHORT" --format json -q '.number')
  if [[ -z "$PROJECT" ]]; then
    echo "Error: Failed to create project." >&2; exit 1
  fi
  gh project link "$PROJECT" --repo "$REPO" --owner "$OWNER" 2>/dev/null || true
  echo "Created and linked project #${PROJECT} to ${REPO}." >&2
fi

CMD="${1:-}"
if [[ -z "$CMD" || ( "$CMD" != "scan" && "$CMD" != "apply" ) ]]; then
  echo "Usage: organize.sh {scan|apply} [--repo OWNER/REPO] [--project NUMBER] [--choices JSON]" >&2
  exit 1
fi

if [[ "$CMD" == "scan" ]]; then
  # Get issue numbers already in the project (for this repo only)
  PROJECT_ISSUES=$(gh project item-list "$PROJECT" --owner "$OWNER" --format json \
    -q "[.items[] | select(.content.repository | endswith(\"${REPO##*/}\")) | .content.number] | sort | .[]" 2>/dev/null || true)

  # Get open issues with milestone and label info
  OPEN_ISSUES=$(gh issue list --repo "$REPO" --state open --limit 100 \
    --json number,title,milestone,labels \
    -q '.[] | "\(.number)\t\(.title)\t\(.milestone.title // "")\t\([.labels[].name] | join(", "))"')

  # Find unorganized issues (not in project)
  UNORGANIZED=""
  while IFS=$'\t' read -r num title milestone labels; do
    [[ -z "$num" ]] && continue
    if ! echo "$PROJECT_ISSUES" | grep -qx "$num" 2>/dev/null; then
      UNORGANIZED+="${milestone:-__none__}"$'\t'"${num}"$'\t'"${title}"$'\t'"${labels}"$'\n'
    fi
  done <<< "$OPEN_ISSUES"

  if [[ -z "$UNORGANIZED" ]]; then
    echo "All open issues are organized in the project."
    exit 0
  fi

  # Group by milestone and print
  CURRENT_MS=""
  COUNT=0
  # Sort by milestone (none last), then by issue number
  SORTED=$(echo -n "$UNORGANIZED" | sort -t$'\t' -k1,1 -k2,2n | sed '/^$/d')

  while IFS=$'\t' read -r milestone num title labels; do
    [[ -z "$num" ]] && continue
    MS_DISPLAY="$milestone"
    [[ "$milestone" == "__none__" ]] && MS_DISPLAY=""

    if [[ "$MS_DISPLAY" != "$CURRENT_MS" ]]; then
      # Count issues in this milestone group
      if [[ -n "$MS_DISPLAY" ]]; then
        COUNT=$(echo -n "$SORTED" | grep -c "^${milestone}"$'\t' || true)
        echo ""
        echo "Milestone: \"${MS_DISPLAY}\" (${COUNT} issues)"
      else
        COUNT=$(echo -n "$SORTED" | grep -c "^__none__"$'\t' || true)
        echo ""
        echo "No milestone: (${COUNT} issues)"
      fi
      CURRENT_MS="$MS_DISPLAY"
    fi

    LABEL_STR=""
    [[ -n "$labels" ]] && LABEL_STR="  [${labels}]"
    echo "  #${num} ${title}${LABEL_STR}"
  done <<< "$SORTED"

  # JSON output for agent parsing
  echo ""
  echo "---JSON---"
  JSON="["
  FIRST=true
  while IFS=$'\t' read -r milestone num title labels; do
    [[ -z "$num" ]] && continue
    [[ "$milestone" == "__none__" ]] && milestone=""
    $FIRST || JSON+=","
    FIRST=false
    JSON+="{\"number\":${num},\"title\":\"${title}\",\"milestone\":\"${milestone}\"}"
  done <<< "$SORTED"
  JSON+="]"
  echo "$JSON"

elif [[ "$CMD" == "apply" ]]; then
  if [[ -z "$CHOICES" ]]; then
    echo "Error: --choices JSON required" >&2; exit 1
  fi

  # Get project ID
  PROJECT_ID=$(gh project list --owner "$OWNER" --format json \
    -q ".projects[] | select(.number == ${PROJECT}) | .id")

  # Get Status field ID
  STATUS_FIELD_ID=$(gh project field-list "$PROJECT" --owner "$OWNER" --format json \
    -q '.fields[] | select(.name == "Status") | .id')

  if [[ -z "$STATUS_FIELD_ID" ]]; then
    echo "Error: Could not find Status field ID" >&2; exit 1
  fi

  # Parse choices JSON with grep/sed (format: {"42": "Todo", "43": "In Progress"})
  # Extract "key":"value" pairs
  PAIRS=$(echo "$CHOICES" | grep -oE '"[0-9]+"\s*:\s*"[^"]+"')

  while IFS= read -r PAIR; do
    [[ -z "$PAIR" ]] && continue
    ISSUE_NUM=$(echo "$PAIR" | grep -oE '^"[0-9]+"' | tr -d '"')
    STATUS=$(echo "$PAIR" | sed 's/^"[0-9]*"\s*:\s*"//; s/"$//')

    [[ "$STATUS" == "Skip" ]] && continue

    # Get option ID for this status
    OPTION_ID=$(gh project field-list "$PROJECT" --owner "$OWNER" --format json \
      -q ".fields[] | select(.name == \"Status\") | .options[] | select(.name == \"${STATUS}\") | .id")

    if [[ -z "$OPTION_ID" ]]; then
      echo "Warning: Unknown status '${STATUS}', skipping #${ISSUE_NUM}" >&2
      continue
    fi

    # Check if already in project
    ITEM_ID=$(gh project item-list "$PROJECT" --owner "$OWNER" --format json \
      -q ".items[] | select(.content.number == ${ISSUE_NUM}) | .id")

    # Add to project if not there
    if [[ -z "$ITEM_ID" ]]; then
      ISSUE_URL="https://github.com/${REPO}/issues/${ISSUE_NUM}"
      ITEM_ID=$(gh project item-add "$PROJECT" --owner "$OWNER" --url "$ISSUE_URL" --format json \
        -q '.id')
      if [[ -z "$ITEM_ID" ]]; then
        echo "Error: Failed to add #${ISSUE_NUM} to project" >&2
        continue
      fi
    fi

    # Set status
    gh project item-edit --id "$ITEM_ID" --field-id "$STATUS_FIELD_ID" \
      --project-id "$PROJECT_ID" --single-select-option-id "$OPTION_ID" >/dev/null
    echo "#${ISSUE_NUM} → ${STATUS}"

  done <<< "$PAIRS"
fi
