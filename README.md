# Claude Code skills

These are skills and subagents for Claude Code that I designed and use in my personal projects. Several files keep the dated rules I added after a run failed. Those rules are the useful part: they turn one bad run into a check that the next run, often on a cheaper model, has to follow.

This is a single-user setup. The measured numbers in these files, such as token costs, thresholds and gaps, come from my own data, except where a file cites its source. Counts quoted from third-party tools, standard accessibility thresholds and tool defaults are not my measurements. Claude Code wrote most of the text and code under my direction. I set the goals, the pass bars and the checks, and I made the decisions.

## Skills

| Skill | What it does | The idea worth copying |
|---|---|---|
| [deep-research](skills/deep-research/SKILL.md) | Researches a topic on the web with one subagent per subtopic, files the synthesis in my notes vault, then offers a learning path or a build plan. | A subject gate before any search, and a counterargument pass for any deliverable that someone will act on. |
| [mm-file](skills/mm-file/SKILL.md) | Files credit-card statements into Money Manager, a self-hosted expense app. The main thread only orchestrates. One subagent per statement reads the PDF and files the rows. | Prove the result: download the database, recompute the card balance offline, and pass only within 1 rupee of the printed amount due. |
| [recall](skills/recall/SKILL.md) | Retrieves context from my notes vault: qmd for passages, Graphify for relationships. | Choose the backend by the shape of the question, cap the main search at 5 results, and keep old snapshots out of default search. |
| [wait-what](skills/wait-what/SKILL.md) | A command I type when an answer did not land. The agent explains it again in plain English and in the terms my notes already use. | Ground the new explanation with one capped lookup in my own notes, and change the framing instead of repeating the same words more slowly. |
| [wrapup](skills/wrapup/SKILL.md) | Files what a session learned into the vault, sweeps for stale claims, and runs a health gate on search and the knowledge graph. | Cost rules with measured numbers come first, and a failed gate is reported line for line, never retried in a loop. |

## Agents

| Agent | What it does | The idea worth copying |
|---|---|---|
| [mm-filer](agents/mm-filer.md) | Files exactly one credit-card statement. It runs on Sonnet with a short tool list. | Its whole final message is a receipt of at most 10 lines, so the main thread never sees the PDF or the rows. |
| [ui-fleet](agents/ui-fleet.md) | Routes UI work to third-party design and testing skills, then builds. | A routing table plus a fixed order: design system first, visual signature second, quality checks last. |
| [wiki-maintainer](agents/wiki-maintainer.md) | Files session outputs and sources into the vault, and keeps its index, log and task board. | One test before cutting any text ("progress is not history"), and volatile facts are checked against a live command, never written from memory. |

## How I write skills

- The description states the trigger, in the words a user would type.
- The rules that came from real failures go first, with their dates.
- The skill ends with a check that proves the result, not a sentence that asserts it.
- The costliest rules carry the measured number that justified them.
- The main thread stays thin: one subagent per unit of work, on a cheaper model, returning a short receipt.
- When only a person can decide, the skill stops and asks.

The patterns, each with an example from these files: [docs/how-i-write-skills.md](docs/how-i-write-skills.md).

## What is left out

- **Scripts that hold personal ids, home paths or scheduler labels.** The skills still name them, but they are not in this repo: the HTTP client of `mm-file` (`mm_api.py`), and the gate and sweep scripts that `wrapup` calls. The one script included is [`verify_db.py`](skills/mm-file/scripts/verify_db.py), which holds no ids and has a built-in `--demo` self-check.
- **My other skills.** This repo is a selection.
- **Third-party skills I use**, such as the design skills that `ui-fleet` routes to. They are not copied here. qmd, Graphify and Obsidian are tools these skills call; I configured them, I did not write them.

## Using them

Copy a skill folder into `~/.claude/skills/` and an agent file into `~/.claude/agents/`. Replace the placeholders, such as `$VAULT`, `<server-ip:port>`, `<connector>` and `<category-id>`. Expect to adapt the paths and commands: these files were written for one person's setup, and some of them call scripts that are not published here.
