#!/usr/bin/env bash
# Post a UTTR (Markdown body only) to the Giscus-backed discussion for a docs page.
# Usage:
#   ./post_uttr_comment.sh --page 01_goals_criteria --body-file /tmp/uttr.md
#   ./post_uttr_comment.sh --page 04_task_seq_1 --body-file -   # stdin
#   ./post_uttr_comment.sh --list
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
MAP="$ROOT/docs/planner-docs/giscus_mapping.json"
PAGE=""
BODY_FILE=""

usage() {
  sed -n '2,8p' "$0" | sed 's/^# //'
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --page) PAGE="${2:-}"; shift 2 ;;
    --body-file) BODY_FILE="${2:-}"; shift 2 ;;
    --list)
      python3 -c "
import json
m=json.load(open('$MAP'))
for k,v in sorted(m['pages'].items()):
  print(f\"{k:28} id={v.get('discussion_id') or 'MISSING':28} #{v.get('number') or '-'}\")
"
      exit 0
      ;;
    -h|--help) usage ;;
    *) echo "unknown arg: $1" >&2; usage ;;
  esac
done

[[ -n "$PAGE" && -n "$BODY_FILE" ]] || usage
[[ -f "$MAP" ]] || { echo "missing $MAP" >&2; exit 1; }

if [[ "$BODY_FILE" == "-" ]]; then
  BODY="$(cat)"
else
  BODY="$(cat "$BODY_FILE")"
fi

# Reject deprecated HTML / split-pane payloads (Giscus is Markdown-only)
if printf '%s' "$BODY" | grep -Eiq '<!DOCTYPE|<html[[:space:]>]|<style[[:space:]>]|uttr-grid|policy-pane|mechanism-pane'; then
  echo "ERROR: body contains HTML/split-pane pollution markers." >&2
  echo "Post GitHub-flavored Markdown only (see docs/templates/uttr-blueprint.md)." >&2
  exit 3
fi

read -r DISCUSSION_ID NUMBER URL < <(python3 -c "
import json,sys
m=json.load(open(sys.argv[1]))
p=m['pages'].get(sys.argv[2])
if not p:
  sys.exit('unknown page slug: '+sys.argv[2])
if not p.get('discussion_id'):
  sys.exit('discussion_id not set for '+sys.argv[2]+'; run bootstrap_giscus_discussions.sh first')
print(p['discussion_id'], p['number'], p['url'])
" "$MAP" "$PAGE") || exit 1

# Prefer GraphQL via gh (same path agents should use)
RESP="$(gh api graphql \
  -f query='mutation($discussionId:ID!,$body:String!) {
    addDiscussionComment(input:{discussionId:$discussionId, body:$body}) {
      comment { id url }
    }
  }' \
  -f discussionId="$DISCUSSION_ID" \
  -f body="$BODY" 2>&1)" || true

if echo "$RESP" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d.get('data',{}).get('addDiscussionComment')" 2>/dev/null; then
  echo "$RESP" | python3 -c "import json,sys; c=json.load(sys.stdin)['data']['addDiscussionComment']['comment']; print('OK', c['url'])"
  echo "discussion: $URL"
  exit 0
fi

echo "GraphQL comment failed (token may lack Discussions write)." >&2
echo "$RESP" | head -c 500 >&2
echo "" >&2
echo "Fallback: use MCP github__discussion_comment_write method=add owner=shayanultra repo=planner discussionNumber=$NUMBER" >&2
echo "Or: gh auth refresh -h github.com -s write:discussion  # classic scopes" >&2
exit 2
