# Language decision

[← Research index](README.md)

The question is not Python vs. TypeScript on merit. Both
[landscapes](landscape-typescript.md) are strong enough. The question is **one
language or two.**

## The three options

### All TypeScript
Shared types with [backstage2](https://github.com/rneventteknik/backstage2), one
toolchain, one deploy target, one dependency culture, one CI setup.

Cost: the weaker data and batch story. The pipeline layer gets built by hand.

### All Python
Better runtime maturity, far better batch pipelines, better memory and MCP
tooling, better durable-execution options on a single Postgres.

Cost: backstage2 becomes a pure HTTP/SQL boundary with hand-maintained types on
both sides.

The chat UI used to be a second cost here — weak in Python, or TypeScript anyway,
making the "one language" benefit illusory. [Adopting Open WebUI](chat-surface.md)
rather than building removes that objection, which strengthens the all-Python
option more than anything else in this file.

### Split — Python core, TypeScript UI
Best tool per layer, connected over AG-UI.

Cost: two deploy targets on Heroku, two CI setups, two dependency ecosystems to
keep patched, and a permanent "where do the shared types live" question.

## The read

The polyglot tax is consistently underestimated by exactly the people who are
comfortable in both languages. And the layer Python wins hardest at — batch
pipelines — is the one needed *last* in the
[build order](architecture-sketch.md#suggested-build-order), not first.

## The question that decides it

**How central are the data pipelines, really?**

- **Centerpiece** — thousands of rows, regular backfills, lineage that matters,
  genuine data engineering. Then Python plus Dagster is a clear win and worth the
  split.
- **Supporting** — "run an LLM over a few hundred rows on a trigger". Then it is a
  hundred lines on a queue, Python's advantage largely evaporates, and sharing
  types with backstage2 is worth more than any of it.

This is the open question with the widest blast radius; see
[open questions](open-questions.md).

---

Next: [MCP topology](mcp-topology.md)
