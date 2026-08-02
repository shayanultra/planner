#!/usr/bin/env bash
# Refresh discussion_id/number/url in giscus_mapping.json from live GitHub Discussions
# by matching discussion title == page pathname.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
MAP="$ROOT/docs/planner-docs/giscus_mapping.json"

EXISTING="$(gh api graphql -f query='
query {
  repository(owner: "shayanultra", name: "planner") {
    discussions(first: 100) {
      nodes { id number url title }
    }
  }
}' --jq '.data.repository.discussions.nodes')"

python3 - "$MAP" "$EXISTING" <<'PY'
import json, sys
map_path, existing_raw = sys.argv[1:3]
mapping = json.load(open(map_path))
by_title = {n["title"]: n for n in json.loads(existing_raw)}
filled = 0
missing = []
for slug, page in mapping["pages"].items():
    title = page["pathname"]
    n = by_title.get(title)
    if not n:
        missing.append(slug)
        continue
    page["discussion_id"] = n["id"]
    page["number"] = n["number"]
    page["url"] = n["url"]
    filled += 1
    print(f"MAP {slug} -> #{n['number']} {n['id']}")

with open(map_path, "w") as f:
    json.dump(mapping, f, indent=2)
    f.write("\n")
print(f"filled={filled} missing={len(missing)}")
if missing:
    print("Still missing (create discussions with exact pathname titles):")
    for s in missing:
        print(f"  - {s}: {mapping['pages'][s]['pathname']}")
    sys.exit(2)
print("READY")
PY
