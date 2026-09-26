# Handover

Session of 23–26 September 2026. Written so a fresh session can pick up the
research without re-deriving the reasoning.

## Where things stand

The repo is **design-phase only** — no code, no stack chosen. It contains
[README.md](README.md) (goals and design principles) and
[research/](research/README.md) (six notes, cross-linked, with a navigation
index).

Nothing in `research/` is a commitment. The two landscape notes deliberately stop
at "here are the options and the trade-off"; the choosing has not happened.

## What this session did

1. Read [backstage2](https://github.com/rneventteknik/backstage2) to ground the
   design — its Gmail integration (OAuth refresh token in settings), calendar
   (API key, read-only, single shared calendar), Slack, the API-key-authenticated
   external API, and its Heroku/Postgres deployment.
2. Sketched the framework's components → `research/architecture-sketch.md`.
3. Surveyed the open-source landscape in TypeScript and Python → two landscape
   notes plus `research/language-decision.md`.
4. Settled MCP server topology → `research/mcp-topology.md`.
5. Evaluated Open WebUI as an adopt-rather-than-build chat surface →
   `research/chat-surface.md`. This changed earlier conclusions; they were updated
   in place rather than left stale.
6. Surveyed non-profit programmes → `research/nonprofit-programs.md`.

## What is actually settled

The five design principles in the README, and:

- **One MCP server per integration boundary**, HTTP transport, identity in the
  transport from day one. See `research/mcp-topology.md`.
- **Adopt a chat surface rather than build one** — Open WebUI unless something
  better appears.
- **Langfuse Cloud over self-hosting**, since the non-profit programme makes it
  effectively free.
- **Heroku offers no non-profit discount**, so infrastructure footprint stays a
  real constraint.

## What is open

`research/open-questions.md` has ten, ordered by blast radius. The one that gates
most others is **#1: how central are the data pipelines?** — because that decides
the language, which decides most of the rest.

## Continuing the research — languages

This is the stated next step. Only TypeScript and Python were surveyed, and the
choice between them was framed as "one language or two". Three candidates were
never examined, and one of them is a strong fit.

### Elixir / BEAM — the strongest unexamined candidate
Worth a real evaluation, not a courtesy paragraph. The framework is largely
"supervise many long-running, crash-prone, stateful concurrent processes", which
is the problem OTP was built for. Specifically worth checking:

- **Supervision trees** against the durable-execution requirement — do they
  replace Temporal/DBOS for our scale, or complement them?
- **Oban** (Postgres-backed jobs) against pg-boss, and **Broadway** against the
  pipeline DSL in the architecture sketch.
- **Phoenix LiveView** as the chat surface — would remove the frontend question
  entirely, which is the thing that made the Python option awkward.
- Against all that: the LLM-ecosystem is thin. Check the state of Anthropic
  clients, MCP server libraries, and structured-output tooling before getting
  attached to the runtime story.

### Gleam — evaluate honestly, there is real prior art
There is more signal here than the repo suggests: `../mcp_packages` is **a Gleam
MCP server already built and running on Cloudflare Workers**, and `../orkestra` is
a Gleam web application with SQLite for another organisation. So the questions are
narrower than "can Gleam do this":

- Does the type system pay off for tool schemas and structured LLM output, or
  fight them?
- What exists for MCP, Anthropic clients and JSON schema generation — and what
  would have to be written?
- Can it sit on BEAM and borrow Elixir's Oban/Broadway, or does that break the
  type story?
- Honest counterweight: ecosystem size against a framework that needs many
  integrations. Note that `.claude/` offers a `gleam-conventions` skill.

### Go and Rust — lower priority, check anyway
Go for the operational story and Temporal-native workflows; Rust for tool servers
where a long-lived, cheap, memory-safe process matters. Both are likely wrong for
the prompt-iteration loop, but that assumption has not been tested.

## Continuing the research — technologies

Not covered at all, roughly in order of how much they would change the design:

- **Model gateways** — LiteLLM, OpenRouter, Portkey. Fallback, routing, cost caps
  in one place rather than in the runtime.
- **Structured extraction** — BAML, Instructor, outlines. The architecture sketch
  calls structured extraction a first-class output and then says nothing about how.
- **Prompt-injection defences** — the sketch states the principle (fetched content
  is data, never instructions) without naming a mechanism. Look at Model Armor,
  Llama Guard, Rebuff, NeMo Guardrails, and what the runtimes offer natively.
- **Cassette/replay libraries** — the eval harness depends on replaying recorded
  tool calls. Nothing was found for this; check whether it genuinely has to be
  written.
- **Retrieval beyond pgvector** — hybrid search, `pg_search`/ParadeDB, plain
  tsvector. Probably still pgvector, but the assumption is untested.
- **Hosting alternatives** — Fly.io, Railway, Render. Only worth the effort
  because Heroku has no non-profit discount; check whether any of them do.
- **Auth and identity** — needed for MCP transport identity. Note
  `../scoutid-keycloak-provider` as prior art.
- **Agent protocols** — A2A, and MCP's own sampling and elicitation, which may
  matter for approvals.

## Prior art in the user's other repos — unexamined

Never opened this session. Worth a look before building anything:

- `../mcp_packages` — Gleam MCP server on Cloudflare Workers (see above)
- `../orkestra` — Gleam + SQLite web app for a different organisation
- `../equipment_list_rag` — Python Gmail downloader with OAuth2; prior art for the
  mail sync path despite the name
- `../googleworkspace-cli`, `../mqtt-meta`, `../analytics-uploader` — unchecked

## Conventions to match

- One topic per file in `research/`, each opening with a `[← Research index]`
  link and closing with a `Next:` pointer.
- `research/README.md` is the navigation index: every file gets a heading link and
  a short paragraph saying what is inside and why to open it. Keep it current.
- Root `README.md` carries a link table. Add a row when adding a file.
- Cross-link between notes, including deep links to specific sections.
- When new research contradicts an earlier note, **update the earlier note** —
  the Open WebUI findings changed four conclusions and each was edited in place.
- Commits: short imperative subject, a paragraph of why, `Co-Authored-By` trailer.

## Method note

A large share of search results in this space is SEO-generated comparison
content, and some of it is confidently wrong. Everything load-bearing here was
checked against a primary source — the GitHub repo, the vendor's own docs, the
licence file. Keep doing that. Vendor blogs comparing themselves to competitors
are flagged as such where cited.

## Practical

- Repo: <https://github.com/rneventteknik/agentic-framework> (public, `main`)
- The `gleam_packages` MCP server is configured for this project in local scope
  (`~/.claude.json`, not committed) — same config as `../orkestra`. A `.mcp.json`
  in the repo root would share it with the team instead.
- No licence file yet; backstage2 is MIT. Open question #10.
