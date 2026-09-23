# Open questions

[← Research index](README.md)

Decisions still outstanding, roughly in order of blast radius.

## 1. How central are the data pipelines?

Decides the [language question](language-decision.md), which decides most of the
rest.

- *Centerpiece* (thousands of rows, backfills, lineage) → Python + Dagster, accept
  the polyglot split.
- *Supporting* (a few hundred rows on a trigger) → all TypeScript, share types with
  backstage2.

## 2. Generic framework, or RN-shaped?

A reusable framework with RN as its first consumer costs perhaps 30% more upfront
in abstraction. **Lean: RN-shaped with clean seams, extract later.**

## 3. Deployment shape

A second Heroku app with the existing Postgres add-on attached, or extra dynos on
the existing app? Second app is cleaner; either way watch the Postgres connection
cap, since a web and a worker dyno on a shared plan eat the allowance quickly.

Open sub-question: separate schema in the same database (assumed) vs. a separate
database entirely.

## 4. Identity model

One service account for all agents, or agents acting as a specific human with that
person's tokens? Shapes the permission model, the audit log, and the MCP transport
auth — see [MCP topology](mcp-topology.md#identity-belongs-in-the-transport-from-day-one).
Painful to retrofit.

## 5. Chat surface first — Slack or web?

Slack is where the ops work already happens and needs no UI build. The web chat is
the better *building and debugging* surface, with the run inspector attached.
Probably both eventually; the question is which one gets built first.

Narrowed by [chat surface](chat-surface.md): adopting Open WebUI makes the web
option nearly free once the MCP servers exist, so this is less either/or than it
looked. The remaining sub-question is whether Open WebUI also replaces a
purpose-built run inspector — probably not.

## 6. Mail trigger latency

Push (Gmail watch via Pub/Sub) or polling? Push is considerably more setup. If a
few minutes of latency is acceptable, polling removes a whole moving part.

## 7. Runtime choice

Deferred until #1 is settled, but the shortlist is written up in the
[TypeScript](landscape-typescript.md#runtime--the-real-fork) and
[Python](landscape-python.md#agent-runtime--deeper-bench-same-conclusion)
landscape notes.

## 8. Observability: self-host or hosted?

Langfuse self-hosted wants ClickHouse + Postgres + Redis, which is heavy next to
one Heroku Postgres. Langfuse Cloud, Laminar, or just our own run store to begin
with?

## 9. Licence

The repo is public and has no licence file yet. backstage2 is MIT — matching it is
the obvious default, but worth an explicit decision.
