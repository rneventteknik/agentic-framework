# Architecture sketch

[← Research index](README.md)

What an agentic framework for our systems needs to contain. Integration-agnostic:
backstage2, mail, calendar and Slack are all just plugins into one integration
layer.

## Shape

```
                 ┌─────────────────────────────────────────┐
 triggers ─────► │  ORCHESTRATION   queue · cron · retries  │
 (cron, webhook, └────────────┬────────────────────────────┘
  event, chat,                │
  manual)         ┌───────────▼─────────────┐  ┌──────────────┐
                  │   AGENT RUNTIME         │◄─┤ POLICY       │
                  │   loop · budget · steps │  │ approvals,   │
                  └────┬───────────────┬────┘  │ caps, scopes │
                       │               │       └──────────────┘
              ┌────────▼──────┐  ┌─────▼─────────┐
              │ TOOL REGISTRY │  │ CONTEXT/MEMORY│
              │ typed, scoped │  │ retrieval,    │
              └────────┬──────┘  │ facts, state  │
                       │         └───────────────┘
        ┌──────────────┼──────────────┬─────────────┐
     ┌──▼──┐       ┌───▼────┐    ┌────▼────┐    ┌───▼───┐
     │mail │       │calendar│    │backstage│    │ slack │  ← integrations
     └─────┘       └────────┘    └─────────┘    └───────┘
                       │
              ┌────────▼─────────────────────────────────┐
              │  RUN STORE  every run, step, tool call,   │
              │  token, cost, outcome → evals, replay,    │
              │  audit, the chat UI's history             │
              └───────────────────────────────────────────┘
```

Two things carry the design: **the tool registry** (one typed definition consumed
by every surface) and **the run store** (everything that happened, durable). With
those right, agents, pipelines, chat, evals and the MCP servers are thin layers.

## Components

### 1. Tool registry
One definition per capability: name, description, input/output schema, handler,
plus metadata the framework actually uses — `read|write`, cost hint, idempotency,
required scope, default approval mode. From one registry, generate Anthropic tool
definitions, MCP servers, HTTP routes and eval fixtures. Tools are the durable
asset; agents are disposable configs around them.

### 2. Integration adapters
Each external system is a package exposing tools plus a *sync* path — pulling data
into our own store. These are different needs and both are wanted: live tools for
"search the inbox now", synced copies so pipelines and retrieval don't hammer the
API. For systems we own, bulk reads can go direct to the database, but writes go
through the owning system's API so its validation and changelog still apply.

### 3. Agent runtime
An agent is a system prompt (versioned file) + tool subset + model + budget + stop
conditions + output schema. The loop handles tool use, structured output, retries,
token and cost accounting, and emits a step event per turn. Keep it behind our own
interface so the underlying SDK stays swappable. Sub-agents fall out naturally: a
tool whose handler runs another agent.

### 4. Policy / human-in-the-loop
What makes this usable in production. Per-tool mode: `auto`, `propose` (agent
produces a draft, a human commits it), `require-approval` (run blocks, resumable).
Plus spend caps per run and per day, a dry-run mode where write tools log instead
of act, and a kill switch. Approvals surface where people already are.

Non-optional once mail is in scope: **untrusted content is untrusted
instructions.** Email bodies, calendar descriptions and customer text are
attacker-controllable in principle. Content fetched by a tool never causes a write
tool to execute on its own say-so, and injected content is tagged as data in the
context rather than merged into the prompt.

### 5. Orchestration / jobs
Durable queue plus scheduler. Triggers: cron, webhook (mail push, calendar watch),
domain events, chat, manual re-run. Needs per-integration rate limiting, backoff,
dead-letter handling, and idempotency keys so a retried job does not send the same
mail twice.

### 6. Data pipelines
A small DSL: `source` (a query or sync cursor) → `map` (LLM call per row,
structured output) → `filter/reduce` → `sink` (write back, notify, materialise a
table). Two execution modes behind one definition: live (triggered, small,
immediate) and batch API (async, roughly half the cost, hours-scale) for
backfills.

The key property is content-hashing each row against the prompt version, so a
re-run only processes what changed. That is what makes iterating on a prompt
across thousands of rows affordable. Every output row keeps its input hash, prompt
version and model, so two pipeline versions can be diffed.

### 7. Context and memory
Layered: structured retrieval (just query the database — usually enough), semantic
retrieval (pgvector over mail, documents, history), and an explicit **facts
store** of structured, citable statements with provenance, which beats stuffing
raw text into context. Plus per-agent scratch state across runs.

### 8. Harness / evals
The part usually skipped, after which iteration stops being possible:

- **Cassettes** — every tool call and result recorded in the run store, so a past
  run can be replayed against a new prompt with no side effects.
- **Suites** — golden tasks with deterministic assertions where possible, an LLM
  judge where not.
- **Regression tracking** — score per prompt and model version over time, so a
  model bump is a measurement rather than a vibe.

### 9. Surfaces
- **Chat UI** — streaming, tool calls visible, run inspector, inline approvals.
  The building and debugging surface. May be adopted rather than built; see
  [chat surface](chat-surface.md).
- **Slack** — the ops surface; agents live in threads where people already are.
- **MCP servers** — the same registry exposed to Claude Code and Claude Desktop.
  The cheapest leverage on the list: an agent for free the day the tools exist.
  See [MCP topology](mcp-topology.md).
- **HTTP API** — for other systems to trigger agents.

### 10. Observability and ledger
Runs, steps, tool calls, tokens, latency, cost, outcome — plus a plain
human-readable audit log ("agent X sent mail Y to Z, approved by A"). One trace id
threaded through everything.

## Additional goals worth adopting

- **Propose-don't-act as the default posture.** An agent whose output is a draft
  is useful on day one at near-zero risk. Autonomy is earned per tool once evals
  exist.
- **Ambient / watcher agents.** Not chat, not batch: something that inspects the
  world on a schedule and speaks only when it has something to say. High value per
  token, and it forces good "when to stay silent" prompting.
- **Natural-language read access over everything.** One query agent across all
  integrations. Cheap, safe, and it proves the tool layer.
- **Structured extraction as a first-class output.** Messy input (mail, PDFs,
  attachments) to typed records. Half the realistic use cases are this rather than
  conversation.
- **Self-documenting framework.** Tool catalogue and agent inventory generated
  from the registry, so humans can still reason about what the fleet can do.
- **Per-user identity from the start.** Even with one organisation, "which human
  is this agent acting as" shapes the token and permission model and is painful to
  retrofit.

## Repository shape

```
agentic-framework/
  packages/
    core/          runtime, registry, run store, policy, types
    integrations/  mail/ calendar/ backstage/ slack/ ...
    pipelines/     batch DSL + executors (live & batch API)
    evals/         harness, cassettes, suites
    mcp/           registry → MCP servers
  apps/
    worker/        queue consumer + scheduler
    api/           webhooks, chat backend, approvals
    web/           chat + run inspector
  agents/          agent definitions & prompts, versioned in git
  migrations/
```

Deployment: a second Heroku app alongside backstage2, the existing Postgres
add-on attached to it as well, everything in its own schema. Watch the connection
cap — a web and a worker dyno on a shared plan eats the allowance quickly, so
small pools or pgbouncer from the start.

## Suggested build order

1. `core` + run store + one trivial agent + a Slack trigger — proves the spine
   end to end.
2. MCP servers over the registry — immediate personal leverage while the rest is
   unbuilt.
3. One batch pipeline over low-risk enrichment data — proves the pipeline layer
   without touching anything that can break.
4. Mail triage in propose-mode with approvals — the first agent that earns its
   keep, and the forcing function for the policy layer.
5. Eval harness, once there are two prompt versions worth comparing. That moment
   arrives sooner than expected.

---

Next: [TypeScript landscape](landscape-typescript.md) · [Python landscape](landscape-python.md)
