#!/usr/bin/env bash
# Create Ideas discussions with Giscus pathname titles and refresh giscus_mapping.json.
# Requires: gh auth with Discussions write (fine-grained: Discussions R/W).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
MAP="$ROOT/docs/planner-docs/giscus_mapping.json"
REPO_ID="R_kgDOTrARYQ"
CAT_ID="DIC_kwDOTrARYc4DCgqB"

if [[ ! -f "$MAP" ]]; then
  echo "missing $MAP" >&2
  exit 1
fi

# List existing discussions (title -> node)
EXISTING_JSON="$(gh api graphql -f query='
query {
  repository(owner: "shayanultra", name: "planner") {
    discussions(first: 100) {
      nodes { id number url title }
    }
  }
}' --jq '.data.repository.discussions.nodes')"

python3 - "$MAP" "$REPO_ID" "$CAT_ID" "$EXISTING_JSON" <<'PY'
import json, os, subprocess, sys

map_path, repo_id, cat_id, existing_raw = sys.argv[1:5]
mapping = json.load(open(map_path))
existing = {n["title"]: n for n in json.loads(existing_raw)}
pages = mapping["pages"]
created = 0
skipped = 0
errors = []

for slug, page in pages.items():
    title = page["pathname"]
    if title in existing:
        n = existing[title]
        page["discussion_id"] = n["id"]
        page["number"] = n["number"]
        page["url"] = n["url"]
        skipped += 1
        print(f"SKIP {slug} -> #{n['number']} {n['id']}")
        continue

    body = f"""## Docs page discussion (Giscus)

- **Slug:** `{slug}`
- **Pathname (Giscus title):** `{title}`
- **Live docs:** {page.get('docs_url', '')}
- **Source:** `{page.get('md', '')}`

### Agent contract
Post **UTTR** tech-transfer comments via GraphQL / `gh` / MCP using `docs/planner-docs/giscus_mapping.json`.
Do **not** use browser automation. Category: **Ideas**.
"""
    query = """
    mutation($repoId:ID!,$catId:ID!,$title:String!,$body:String!) {
      createDiscussion(input:{
        repositoryId:$repoId, categoryId:$catId, title:$title, body:$body
      }) {
        discussion { id number url title }
      }
    }
    """
    proc = subprocess.run(
        [
            "gh", "api", "graphql",
            "-f", f"query={query}",
            "-f", f"repoId={repo_id}",
            "-f", f"catId={cat_id}",
            "-f", f"title={title}",
            "-f", f"body={body}",
        ],
        capture_output=True,
        text=True,
    )
    raw = proc.stdout.strip() or proc.stderr.strip()
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        errors.append((slug, raw[:300]))
        print(f"FAIL {slug}: non-JSON response: {raw[:200]}", file=sys.stderr)
        continue

    if data.get("errors") or not data.get("data", {}).get("createDiscussion"):
        msg = data.get("errors", data)
        errors.append((slug, str(msg)[:300]))
        print(f"FAIL {slug}: {msg}", file=sys.stderr)
        continue

    d = data["data"]["createDiscussion"]["discussion"]
    page["discussion_id"] = d["id"]
    page["number"] = d["number"]
    page["url"] = d["url"]
    existing[title] = d
    created += 1
    print(f"CREATE {slug} -> #{d['number']} {d['id']}")

with open(map_path, "w") as f:
    json.dump(mapping, f, indent=2)
    f.write("\n")

print(f"\nDone. created={created} skipped={skipped} errors={len(errors)}")
print(f"Wrote {map_path}")
if errors:
    print("\nToken needs Discussions write. Fine-grained PAT: Repository permissions → Discussions → Read and write.", file=sys.stderr)
    print("Then re-run: docs/planner-docs/scripts/bootstrap_giscus_discussions.sh", file=sys.stderr)
    sys.exit(2)

# readiness: all pages must have IDs
missing = [k for k, v in pages.items() if not v.get("discussion_id")]
if missing:
    print("Missing IDs:", ", ".join(missing), file=sys.stderr)
    sys.exit(3)
print("READY: all page discussion_ids populated")
PY
