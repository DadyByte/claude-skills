---
name: deep-research
description: Deep research any topic from the web, synthesize it, save a wiki note, then produce a learning path or build plan. Use when the user says "deep research X", "research X and help me build/learn it", or invokes /deep-research.
argument-hint: <topic> [--learn | --build] [--deep]
---
<!-- Public copy. Personal paths, names and ids are replaced with placeholders. -->

# Deep Research

Pipeline: scope → research → synthesize → retain → act.

## Step 0: Scope

### 0a. Subject gate — runs BEFORE any searching

If the research is *about* or *for* a specific person, company, product, or codebase, you must know who or what it is before a single search. Researching first and assuming the subject produces a confident, well-sourced deliverable aimed at the wrong target — the most expensive failure this pipeline has.

1. **Verify what is verifiable.** A named person → read their public profile. A company → their site and filings. A repo → read it. One call, up front.
2. **Name the constraints that would change the answer**, and ask them together in a single `AskUserQuestion` — location, budget, timeline, hard exclusions, anything contractual. Ask only what changes the work; skip what has a sensible default.
3. **Write the verified facts and locked constraints down** before Step 1, and treat them as fixed for the rest of the session.

Skip 0a only for genuinely subject-free topics ("how does TLS session resumption work").

### 0b. Intent

Infer from arguments: `--learn` (understand deeply), `--build` (make something with it). Neither given and intent unclear from conversation → fold the question into the Step 0a batch rather than asking separately. Break the topic into 1–3 subtopics max.

## Step 1: Research (route by topic type)

- **Library / framework / SDK / API / CLI tool** → Context7 first: `resolve-library-id` then `query-docs` (one call per concept). Web research only fills gaps Context7 misses (community opinion, comparisons, real-world pitfalls).
- **Everything else** → spawn `general-purpose` agent(s) with WebSearch + WebFetch. One agent per subtopic, max 3 in parallel. Keeps raw pages out of main context — only synthesis returns.
- **JS-heavy pages that a plain fetch cannot render** → Apify `rag-web-browser` MCP tool as fallback.
- **Login-walled pages** → ask the user, then use claude-in-chrome if the site's terms allow it; WebFetch cannot. Never proceed on an assumption.
- **`--deep`** → up to 5 subtopics/agents, each agent must consult 8+ sources, and add a second-pass agent that hunts for counterarguments and gaps in the first-pass findings.

**Does the topic have live discussion?** `last30days` only earns a call when the answer lives in what people said recently — tooling in flux, product sentiment, market reaction, trends, controversies. It returns noise for stable professional knowledge (how to read an engineering drawing, how a legal process works, established craft), because the answer lives in books, filings and practice rather than forums. If a run comes back with low on-topic yield, **diagnose tool-topic fit before re-tuning the query** — two re-runs on a topic with no social footprint is two wasted runs, and the third tells you nothing the first did not.

Source tiers (prefer higher, note tier when sources conflict): T1 official docs/specs/papers/source code > T2 established tech press and recognized experts > T3 blogs/tutorials > T4 forums/social. A claim resting only on T3/T4 gets flagged as weakly sourced.

As each agent returns, append its findings to a checkpoint file in the scratchpad (`deep-research-<topic-slug>.md`) before spawning the next step — survives context compaction; resume from it instead of re-researching.

Every research agent prompt MUST require:
1. Prefer primary sources (official docs, specs, papers, source code) over blog spam.
2. Note publication dates; flag anything stale or version-specific.
3. Flag contradictions between sources instead of silently picking one.
4. Return a source URL for every non-obvious claim.
5. Return a ranked "best 5 resources to go deeper" list.

## Step 2: Synthesize

Merge agent outputs into one report:

1. **TLDR** — 3 sentences.
2. **Mental model** — the core idea that makes everything else click.
3. **Key concepts** — short definitions, how they relate.
4. **How it works in practice** — ecosystem, tooling, typical workflow.
5. **Pitfalls & tradeoffs** — what bites beginners, what experts argue about.
6. **Best sources** — ranked, with one line on why each earns its spot.

## Step 3: Retain

Read `$VAULT/CLAUDE.md` for the vault schema, then file the synthesis per its Output filing op: a `synthesis` page in the owning project folder (or global `wiki/` if cross-project), update `wiki/index.md`, append to `wiki/log.md`, run the stale-page sweep. Link related existing pages. Tell the user the page path. (Not a `type: note` page — those are remember.py quick captures.)

## Step 4: Act

- `--learn` → ordered learning path: resources in sequence, a small exercise per stage, milestones to know you've got it.
- `--build` → spawn `Plan` agent with the synthesis as context; return a build plan (steps, stack choice, critical decisions). Do not start building until the user approves the plan.
- Neither flag → stop after Step 3, offer both.

## Rules

- Research agents do the reading; main thread only sees synthesis.
- No claim without a source. No source dump without ranking.
- If research contradicts an assumption stated by the user, surface it explicitly.
- **Any research producing a large deliverable — a plan, a curriculum, a recommendation someone will act on — gets the `--deep` counterargument pass, whether or not `--deep` was typed.** Its value is that a cold reader does not share the first pass's priors: it is the check that catches a wrong premise before the deliverable is handed over. Where the harness forbids spawning agents unprompted, say so and run the pass inline against your own draft, hunting specifically for the assumption you never verified.
- State every unverified assumption the deliverable rests on, in the deliverable, at the point it matters. An assumption that stays in your head is one nobody can correct.
