# Agent access: Giscus / Discussions UTTR injection

## Purpose

Agents post **UTTR** tech-transfer comments to the correct GitHub Discussion for each MkDocs page **without browser automation**.

## Read first

| Artifact | Path |
|----------|------|
| Static ID map | `docs/planner-docs/giscus_mapping.json` |
| UTTR HTML template | `docs/templates/uttr-blueprint.md` |
| Giscus widget config | `docs/planner-docs/overrides/partials/comments.html` |

## Giscus alignment (must match)

- Repo: `shayanultra/planner` (`R_kgDOTrARYQ`)
- Category: **Ideas** (`DIC_kwDOTrARYc4DCgqB`)
- Mapping: **pathname** + **strict**
- Discussion **title** must equal page pathname, e.g. `/planner/01_goals_criteria/`

## Bootstrap (one-time, human or agent with write scope)

```bash
# Fine-grained PAT needs: Discussions → Read and write on shayanultra/planner
# Or classic: write:discussion
docs/planner-docs/scripts/bootstrap_giscus_discussions.sh
# or after manual UI creates:
docs/planner-docs/scripts/sync_giscus_mapping.sh
```

Until bootstrap succeeds, `pages.*.discussion_id` may be `null`.

## Post a UTTR

```bash
docs/planner-docs/scripts/post_uttr_comment.sh \
  --page 01_goals_criteria \
  --body-file /path/to/uttr.md
```

### MCP fallback (comment only)

**Prefer MCP `github__discussion_comment_write` when `GH_TOKEN` is set** (fine-grained PATs often lack Discussions write and make `gh` / `post_uttr_comment.sh` fail with FORBIDDEN).

When `gh` GraphQL is forbidden but MCP works:

- Tool: `github__discussion_comment_write`
- `method=add`, `owner=shayanultra`, `repo=planner`
- `discussionNumber` from mapping `pages[slug].number`
- `body` = UTTR payload

MCP does **not** create discussions; bootstrap still required once.

## Deep-research session gate

Ready when:

1. All 11 split pages (+ index/AGENTS/RAGnaroX) have non-null `discussion_id` in the map.
2. `post_uttr_comment.sh --page 01_goals_criteria --body-file …` returns OK (or MCP add succeeds).
3. Agent never uses browser tools for Giscus.

## Manual discussion titles (if creating in UI)

Create under **Ideas** with **exact** titles:

```
/planner/
/planner/01_goals_criteria/
/planner/02_system_overview/
/planner/03_architecture_overview/
/planner/04_task_seq_1/
/planner/05_task_seq_2/
/planner/06_tooling/
/planner/07_implementation/
/planner/08_user_flow/
/planner/09_readiness/
/planner/10_sources/
/planner/11_citation/
/planner/AGENTS/
/planner/RAGnaroX/
```

Then run `sync_giscus_mapping.sh`.
