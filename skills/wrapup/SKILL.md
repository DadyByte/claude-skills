---
name: wrapup
description: Force Agent OS capture of the current session now — file durable knowledge into the vault, update the tasks board. Use when the user says "/wrapup", "wrap up", "save this session", or before ending a session whose knowledge must not wait for auto-capture.
---
<!-- Public copy. Personal paths, names and ids are replaced with placeholders. -->

# Wrapup — force session capture + filing

## Cost rules — read first, they are the whole point

Two wrapups on 2026-08-02 cost ~187k tokens between them. Measured causes, in order:

1. **`wiki/log.md` is past 120 KB and is append-only** (123.7 KB / 81 entries —
   `ls -lh`, `grep -c '^## \['`, 2026-08-03; it only grows). NEVER `Read` it.
   Append with `cat >> "$VAULT/wiki/log.md" << 'EOF'`. Reading it to
   "check the format" costs ~30k tokens to learn a heading pattern documented here:
   `## [YYYY-MM-DD] <op> | <title>`.
2. **Never `Read` a whole page to find one line.** `Grep` for the anchor, then
   `Edit`. One project alone is 96 KB across five pages.
3. **Never re-read a file you just edited.** Edit fails loudly if the anchor is
   missing; a verification read is pure cost.
4. **Prefer one Bash script over ten tool calls.** `sweep.py` is the pattern.

## Steps

1. **Write the drop yourself** (no subprocess):
   `$VAULT/inbox/YYYY-MM-DD-HHMM-<slug>.md`, sections `# <title>`,
   `## What happened`, `## Decisions`, `## Open follow-ups`, `## Candidate tasks`
   (`- [ ] <task> — #<project> — YYYY-MM-DD`). Durable knowledge only — decisions,
   findings, state. Not process narration.
   **Add `## Files already updated this session`** listing every path this session
   already wrote. This is what lets the next step skip discovery entirely.

   **If the session was long enough to be compressed, your context IS a summary — do
   not write the drop from memory.** Reconstruct it from what was recorded while the
   work was fresh: `git log --oneline <base>..HEAD` and the commit bodies, any ledger
   or progress file the session kept, the plan/spec it worked from. Mine those first,
   then add only what they cannot know.
   Measured 2026-08-18: a 12-task build's incremental ledger held **24** deferred
   items; the drop written from compressed context at the end carried **3**. Four of
   five spot-checked findings existed nowhere but the ledger. The wrapup looked
   complete and lost ~88% of its findings — a failure mode indistinguishable from
   success unless you diff the drop against the contemporaneous record.

2. **Decide whether an agent is needed at all.** This is the biggest single lever.
   - **The session already filed its own changes** (edited the project pages as it
     went, which is the normal case for a long working session) → **do steps 3-5
     yourself. Do not dispatch.** An agent would spend 80-100k tokens
     rediscovering edits you made and can already see.
   - **The drop carries knowledge nobody has filed yet** — several stale drops, an
     ingest, or a session whose findings never reached a page → dispatch
     `wiki-maintainer`, with the template below.

3. **Index, log, tasks** — mechanical, do them directly:
   - `wiki/log.md`: append via heredoc. Never read.
   - `wiki/index.md`: `Grep` the page name, `Edit` that line. Add a line for any
     new page.
   - `tasks/new.md`: append new items; reword rather than duplicate existing ones.
   - Delete the drop once its content is on a page.

3b. **Rewrite the project brief** — `projects/<name>/<name>-brief.md`, for every project whose current
   truth this session changed: what is built, a decision made or reversed, an open item closed or opened,
   a step that is now the user's. Edit the affected sections in place and bump `updated:`; never append a
   dated block — the narrative goes to `log.md`, the brief only says what is true now. A project with three
   or more pages and no brief gets one (format: any existing brief, such as the Agent OS brief). The gate
   prints `MISSING`/`STALE brief` lines from `brief_status.py`; clearing them is this session's job, not the user's.

4. **Cross-tree sweep** — `python3 ~/.claude/skills/wrapup/sweep.py --roots "<project repo>" -- "<regex>" …`,
   one regex per claim the session **corrected** (not per topic it touched). It
   scans the vault, agent memory and any repo roots you add, splitting hits into
   "needs eyes" and "near correction language". Read every hit; roughly a third
   are legitimate history. Fix what survives triage, then re-run.

4b. **Artefact sweep — what did I CHANGE, and which page documents it.** Step 4 finds
   claims you corrected. It cannot find a page that went stale because the system
   moved under it: nothing was corrected there, so no regex describes it. On
   2026-09-21 a wrapup passed step 4 clean and still left the operations page of
   another project describing one scheduled job when there were two, and two details of a
   fetch step that the code had since changed — the page a
   future session reads first to diagnose that project.
   ```bash
   python3 ~/.claude/skills/wrapup/artefact_sweep.py --days 3
   ```
   It maps every file the session's repos changed onto the vault pages that name it,
   and flags a page whose `updated:` predates the change. **Every page it prints is
   one you either update or consciously leave** — say which in step 6. The rule of
   thumb it mechanises: *a page that describes how something works is stale the
   moment that thing changes, and only you know you changed it.*

5. **Agent OS refresh gate — ALWAYS, on BOTH paths.** Filing changes the corpus,
   so the index and the retrieval benchmark must be re-run whether or not you
   dispatched an agent:
   ```bash
   bash ~/.claude/skills/wrapup/agent_os_refresh.sh
   ```
   It prints one OK/FAIL line per step and exits non-zero if any failed.
   **Run it even when you filed nothing** — a no-op wrapup still proves the index
   is healthy, and that is the only cheap signal you get.
   If it reports FAIL, **relay those lines verbatim in step 6 and do not call the
   wrapup clean.** Do not retry it in a loop and do not re-run it with stderr
   hidden; filing already succeeded, so a red gate is a report, not a rollback.
   A red `prove_recall` usually means a page this session wrote now outranks the
   page that holds the answer — fix the page, never the benchmark question.
   A `STALE … map` line is not a failure, and it is never silent.
   The gate's viewer-rebuild step (labelled `<knowledge-base>_rebuild` in its output) redraws the graph viewer from whatever `graph.json` holds, so
   its OK does **not** mean the knowledge base's map is current. On 2026-10-04 a
   wrapup reported the knowledge base updated while the map was 9 days and 14 files
   behind; the user caught it.

6. **Relay** what was filed, which tasks changed, what the sweep caught, which briefs were
   rewritten, and the Agent OS refresh result line.
   **Always say which knowledge-base layers are current.** Search (`/recall`, qmd)
   is fresh after every gate. The map (both Graphify graphs and the graph
   viewer) is fresh only when the gate prints `OK … map`. On a `STALE` line, name
   the refresh as the user's step with the file count and the exact command, and
   recommend now or later — later when another session is about to change the
   same pages, so one refresh covers both.

## Agent dispatch template — only when step 2 says so

> Digest `inbox/<drop>` into proper pages, then update index, log and tasks.
> **Cost rules: never Read `wiki/log.md` (120 KB+, append-only — use `cat >>`).
> Never Read a whole page to change one line — Grep the anchor, then Edit. Never
> re-read a file you just edited.**
> The drop's "Files already updated this session" list is authoritative — those
> paths are current, do not re-verify them.
> For the stale sweep use `python3 "$VAULT/.claude/scripts/find_stale.py" <drop>`,
> which returns the pages closest to the drop via qmd, instead of grepping the
> vault blind.
> Report what you filed, what you fixed, and any contradiction you could not resolve.

## Why the cross-tree sweep exists (step 4)

On 2026-08-01 three claims were corrected across the wiki and every one survived
in a separate project repo, because the stale sweep only grepped the vault. A
later pass found eight more, including two task-board entries that contradicted
the project's `plan.md`, and then agent memory as a third tree nobody had swept.
**Corrections live wherever the project lives, not only where the notes live**,
and a claim fixed only on the page in front of you is not fixed.

## Page hygiene — the compounding cost

One project's system page reached 28 KB because every correction *appended* a
warning block instead of editing the claim. Every future wrapup pays that size.
**Correct the claim in place and leave one short dated note; the narrative
belongs in `log.md`,** which is append-only and never read.

Graph: Graphify owns the vault graph. Since 2026-10-25 a weekly job
(`com.example.agent-os-graph`, Tuesday 03:30, `graph_refresh.py`) refreshes a stale map
itself, so a refresh is never part of a wrapup. Refresh by hand with `/graphify . --update`
only when the user asks, or when the gate's map line (step 5) says the job is not loaded,
its last run was restored or failed, or it will skip the map as too big (more than
`MAX_FILES` changed pages; since 2026-11-02 the line prints the job's own decision from
`graph_refresh.py --forecast`) — decided by that line, not by memory. That refresh is
the user's step: `/graphify . --update` typed in the Claude chat box, in a session started in
the map's folder.
