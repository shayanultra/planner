#!/usr/bin/env bash
# Acceptance: each docs page's Giscus binding resolves a discussion with UTTR content.
# Success = giscus.app API for that page term returns comments matching UTTR/RAGnaroX
# (proxy for "visible on https://shayanultra.github.io/planner/<page>/").
# Also fails if UTTR-matching comments still contain HTML pollution markers.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
MAP="$ROOT/docs/planner-docs/giscus_mapping.json"
REPO="shayanultra/planner"
CATEGORY="Ideas"
FAIL=0

python3 - "$MAP" <<'PY'
import json, sys, urllib.parse, urllib.request

map_path = sys.argv[1]
m = json.load(open(map_path))
pages = m["pages"]
# 11 split pages only (core contract)
required = [
    "01_goals_criteria",
    "02_system_overview",
    "03_architecture_overview",
    "04_task_seq_1",
    "05_task_seq_2",
    "06_tooling",
    "07_implementation",
    "08_user_flow",
    "09_readiness",
    "10_sources",
    "11_citation",
]

fail = 0
for slug in required:
    page = pages[slug]
    number = page.get("number")
    pathname = page.get("pathname")
    if not number:
        print(f"FAIL {slug}: missing discussion number in mapping")
        fail += 1
        continue

    # Prefer number mapping (matches comments.html)
    q = urllib.parse.urlencode(
        {
            "repo": "shayanultra/planner",
            "term": str(number),
            "number": str(number),
            "category": "Ideas",
            "mapping": "number",
        }
    )
    url = f"https://giscus.app/api/discussions?{q}"
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except Exception as e:
        print(f"FAIL {slug}: giscus API error {e}")
        fail += 1
        continue

    disc = data.get("discussion") or {}
    count = disc.get("totalCommentCount") or 0
    comments = disc.get("comments") or []
    bodies = " ".join((c.get("bodyHTML") or c.get("body") or "") for c in comments)
    raw_bodies = " ".join((c.get("body") or "") for c in comments)
    # bodyHTML is rendered HTML from Giscus API — pollution check uses raw body when present
    pollution_src = raw_bodies if raw_bodies.strip() else bodies
    # also pull via number-only — if empty, try pathname for diagnostics
    has_uttr = ("UTTR" in bodies) or ("RAGnaroX" in bodies) or ("ragnarox" in bodies.lower())
    # Raw HTML chrome that must not appear in Markdown UTTR comments
    pollution_markers = (
        "uttr-grid",
        "policy-pane",
        "mechanism-pane",
        "ragnarox-uttr",
        "<!DOCTYPE",
    )
    # Only flag if markers appear as author-authored chrome (class names / doctype),
    # not incidental words in rendered HTML from Giscus.
    polluted = any(m in pollution_src for m in pollution_markers)

    docs_url = page.get("docs_url") or f"https://shayanultra.github.io{pathname}"
    if count < 1:
        print(f"FAIL {slug}: discussion #{number} has 0 comments (docs: {docs_url})")
        fail += 1
        continue
    if not has_uttr:
        print(
            f"WARN {slug}: #{number} has {count} comment(s) but none match UTTR/RAGnaroX yet (docs: {docs_url})"
        )
        # treat missing UTTR as fail for full transfer acceptance
        fail += 1
        continue
    if polluted:
        print(
            f"FAIL {slug}: #{number} UTTR present but HTML pollution markers remain (docs: {docs_url})"
        )
        fail += 1
        continue

    print(f"PASS {slug}: #{number} comments={count} UTTR=yes clean-md=yes docs={docs_url}")

print("---")
if fail:
    print(f"RESULT FAIL ({fail} page(s))")
    sys.exit(1)
print("RESULT PASS (all 11 pages bound with UTTR content)")
sys.exit(0)
PY
