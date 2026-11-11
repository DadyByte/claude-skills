---
name: wait-what
description: Stop. That last message did not land — re-pitch it in the wiki's own words.
disable-model-invocation: true
---
<!-- Public copy. Personal paths, names and ids are replaced with placeholders. -->

Wait — I don't understand where you've got to here.

Before you re-pitch, ground yourself in my vocabulary. Run one capped lookup on the topic of that last message:

```bash
qmd query "<topic of the last message>" --json -n 5
```

Read the snippets. Take the terms I actually use for this — project names, decisions already made, the names I gave things. If qmd returns nothing useful, fall back to `/recall` for the same topic. If both come back empty, say so in one line and re-pitch anyway.

Now re-pitch that:

- **Give me context first.** Where are we, and why does this step exist? One short paragraph before any detail.
- **Use ASD-STE100 Simplified Technical English.** Approved plain words. Active voice. One idea per sentence.
- **Use the ubiquitous language from the wiki.** My names for things, not generic ones. If a wiki page already settled this, name the page.
- **Do not repeat the message that failed.** A slower version of the same words will fail the same way. Change the framing.

Keep paths and commands exact.
