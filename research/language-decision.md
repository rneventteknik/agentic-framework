# Language decision

[← Research index](README.md)

The question is not Python vs. TypeScript on merit. Both
[landscapes](landscape-typescript.md) are strong enough. The question is **one
language or two.**

## The options

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

### All Gleam
Added after the [Gleam landscape](landscape-gleam.md) survey, and a more serious
option than it first looked: two Gleam codebases already run in the organisation
(`../mcp_packages`, `../orkestra`), so the "can we ship it" risk is largely retired.
One language across runtime, MCP servers, API and — via `lustre` server components —
the web surface, on a runtime built for supervising crash-prone concurrent work.

Cost: the largest build-it-ourselves bill of any option. Every integration SDK is
ours to write, the durable queue is either a three-day-old package or Oban over
untyped FFI, and the LLM client is a well-formed but unmaintained binding we would
expect to vendor.

This also breaks the "share types with backstage2" argument that carries the
TypeScript option, without buying Python's pipeline strength.

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

Gleam sits outside that question rather than inside it — it loses on pipelines
either way. It is decided by a second one: **how much of the foundation are we
willing to own?** Gleam wins the runtime and costs integration SDKs, a queue and a
maintained LLM client. Answer "as little as possible" and it is out; answer "we
intend to vendor and maintain a spine anyway" and it becomes the strongest option
on the list. See the [Gleam landscape](landscape-gleam.md#the-honest-counterweight).

---

Next: [MCP topology](mcp-topology.md)
