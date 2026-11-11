---
name: recall
description: Deep context retrieval from the vault (the personal knowledge base) and the Claude setup graph. Use when past decisions, project history, prior research, or how the setup is wired would help and is not already in context — or when the user says "recall X", "what did we decide about X", "check the wiki".
---
<!-- Public copy. Personal paths, names and ids are replaced with placeholders. -->

# Recall — RAG context retrieval (v3: qmd + Graphify)

Two retrieval backends. Pick by what the question needs; they compose.

- **qmd** — semantic passage search over the vault. Best for "what do we know / decide / say about X" — meaning-level lookup that returns the exact lines.
- **Graphify graph-RAG** — relationship and structure. Best for "how does X connect to Y", "what depends on X", "trace the flow", "what's in the same cluster". Two graphs:
  - Vault: `$VAULT/graphify-out/graph.json` — projects, decisions, research.
  - Claude setup: `$HOME/.claude/graphify-out/graph.json` — skills, agents, rules, memory (how the setup itself is wired).

## Path A — qmd (semantic, default for content questions)

1. `qmd query "<the actual question, in natural language>" --json -n 5` (always cap — default 20 burns ~10x tokens).
2. From the JSON (docid, path, score, snippet, context), pick the top 3–5.
3. Fetch only the answering section: `qmd get "#<docid>:<line-10>:40"`. Full `qmd get "<path>"` only if the section isn't enough.
4. Answer citing page names. Quote only what's needed.
5. Weak results? Retry once as keyword: `qmd search "<2-4 keywords>"`.
6. Read each hit by kind. A brief or living page is current truth. A progress record (audit, results, debrief, scan, ledger, fixed-bug write-up) is a dated fact about what happened: it answers "what was done / found / measured" and stays in default search, but check the brief before citing its numbers as current. Never call a progress record stale or out of date because it is dated or finished.
7. Replaced plans and the old wording of pages only ("what did we think in August", "why was X dropped"): add `-c history`. That collection holds dated snapshots (`projects/<name>/history/`) and rotated log months (`wiki/log/`). It is never searched by default, because a snapshot outranks the current brief. Never answer a current-state question from it.

## Path B — Graphify (relationships, structure, "how is this wired")

Preferred: the **Graphify MCP tools** (deferred — load via ToolSearch `"graphify graph"` first). Two servers, pick by graph:
- Vault question (projects/decisions/research): the `mcp__<connector>__*` tools of the vault graph server.
- Setup question (which skill/agent/rule/memory does X, how they connect): the `mcp__<connector>__*` tools of the setup graph server.
- Core tools: `query_graph` (BFS/DFS search), `shortest_path` (link between two concepts), `get_node` / `get_neighbors`, `get_community`, `god_nodes`, `graph_stats`. Results cite `source_location`; open those pages for full text.

CLI fallback (MCP server down): `cd "$VAULT" && graphify query "<question>" --budget 1500` (or `$HOME/.claude` for setup); `--dfs` traces one chain; `graphify path "A" "B"`.

Reach for Path B when the answer is about connections rather than a passage, or when qmd returns scattered hits that don't cohere — the graph shows how they relate. For a plain content lookup, Path A is cheaper; don't rebuild or over-traverse.

## Both paths down (qmd erroring AND no graph)

- Grep `wiki/index.md` for topic terms, read the top 3–5 pages it points to.

## Either path

- New synthesis worth keeping? Offer to file it per vault CLAUDE.md (dispatch wiki-maintainer).
- Nothing surfaces but the topic should exist? Check `tasks/`, `wiki/log.md` and `qmd query "<q>" -c history` directly before saying the wiki has no record.
- Graph stale (pages changed since last build)? `/graphify . --update` from that dir refreshes incrementally — offer it, don't auto-run (extraction costs tokens). Not `graphify --update` (no such flag); not `graphify update <dir>` (code-only, silently skips markdown).
