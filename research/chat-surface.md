# Chat surface — build or adopt

[← Research index](README.md)

The [architecture sketch](architecture-sketch.md#9-surfaces) lists chat as one of
four surfaces and assumes we build it. [Open WebUI](https://github.com/open-webui/open-webui)
is the case for not building it at all, and it changes the
[language decision](language-decision.md) as a side effect.

## What Open WebUI is

A finished, self-hosted AI chat product — ~153k stars, Svelte/TypeScript frontend,
Python/FastAPI backend, SQLite or Postgres. Multi-user auth and RBAC,
conversation history, model switching, knowledge bases and RAG, all working out of
the box.

It is a chat **product**, not an agent framework. That distinction is the whole
analysis.

## Why it fits our design unusually well

**Native MCP over Streamable HTTP.** Since v0.6.31 Open WebUI connects to MCP
servers natively, [Streamable-HTTP only](https://docs.openwebui.com/features/extensibility/mcp/)
(stdio and SSE need the `mcpo` proxy). That is exactly the transport the
[MCP topology](mcp-topology.md#transport) already commits to, for independent
reasons.

**It solves the identity problem we flagged.** Auth modes are none, bearer token,
OAuth 2.1 with dynamic client registration, or static OAuth — plus custom headers
with `{{USER_ID}}`, `{{USER_EMAIL}}` and `{{USER_ROLE}}` template tokens. That
propagates the *human's* identity into our policy layer without building an
identity broker, which is the thing
[mcp-topology.md warns is painful to retrofit](mcp-topology.md#identity-belongs-in-the-transport-from-day-one).

**It removes the layer Python is worst at.** If the chat surface is adopted rather
than built, the "Python buys you Python plus a TypeScript frontend" objection in
the [language decision](language-decision.md) mostly dissolves.

**It compresses the build order.** Chat was step 5-ish; with Open WebUI it comes
free at step 2. Build the MCP servers, point Open WebUI at them, and the chat-
interface goal is met at near-zero marginal cost.

## Where it stops

**It is a surface, not the framework.** No agent runtime, no scheduled or ambient
agents, no pipelines, no run store, no evals. Everything in the architecture
sketch except surface #1 still has to exist.

**No run inspection.** It shows conversations, not agent traces, per-step token
and cost accounting, or cassettes. The run inspector stays ours (or Langfuse's).

**No human-in-the-loop tool gating.** Tool calls execute; there is no propose-and-
wait. This is not a flaw to work around — it is the argument for
[policy under the registry](mcp-topology.md#policy-runs-server-side-under-the-registry)
made concrete. We do not control this client, so the server must enforce.

A tempting shortcut is exposing "approve proposal X" as a tool. It does not work:
an approval mediated by an LLM's summary is not an approval. The human has to see
the actual draft or diff, which means approvals link out to a small purpose-built
page regardless of chat surface.

**Operational friction.** MCP servers can only be registered by admins. OAuth 2.1
tools cannot be pre-enabled on a model, because they need interactive browser auth
mid-chat. And it is another substantial application to run and upgrade — its own
database, its own auth, ~18.7k commits of surface area.

## Licence — read before committing

Open WebUI moved from BSD-3-Clause to a
[custom "Open WebUI License" in v0.6.6](https://docs.openwebui.com/license/)
(April 2025). Still permissive and free to self-host, but it requires preserving
visible "Open WebUI" branding unless one of three conditions holds: fewer than 50
end users in any rolling 30-day period, written permission, or a paid enterprise
licence.

For RN the under-50 exemption almost certainly applies, so this is a non-issue in
practice. Two caveats worth recording anyway: it is **not** an OSI-approved open
source licence, and the licence has already changed once in a restrictive
direction — a vendor-risk signal, not a dealbreaker.

## How this differs from n8n and Dify

The [TypeScript landscape](landscape-typescript.md#what-to-skip) recommends
skipping the low-code platforms, which could look inconsistent. It is not: those
ask us to *build agents inside a GUI*, putting prompts and logic outside git.
Open WebUI asks for nothing — it is a client that talks to our MCP servers. The
agents, prompts and policy stay exactly where they were.

## Verdict

**Adopt as the chat surface; do not mistake it for the framework.** It is a client
of our MCP servers, never a place agents get built.

Open sub-questions: whether it replaces a purpose-built run inspector (probably
not) and whether Slack still comes first for ops work (probably yes — see
[open questions](open-questions.md)).

---

Next: [Open questions](open-questions.md)
