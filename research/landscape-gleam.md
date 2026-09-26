# Open-source landscape — Gleam

[← Research index](README.md) · Surveyed September 2026

Mapped against the layers in the [architecture sketch](architecture-sketch.md).
Every package claim here was checked against the Hex API, the Gleam package
index and the upstream repository — see [method](#method-and-a-warning-about-hex-search).

## Headline

Gleam is **viable for the spine and thin at the edges**, and the split is sharper
than in [TypeScript](landscape-typescript.md) or [Python](landscape-python.md).

The platform layer — language, OTP, HTTP, Postgres, SQL, migrations, UI — is real,
maintained by the core team, and in production in
[`../orkestra`](#prior-art-in-the-users-own-repos). The LLM layer is a field of
one-author packages published in a single burst and never touched again. Nothing
in the agentic layer has a second contributor, and the two pieces that would carry
the most weight — a durable job queue and a tool-schema library — are both under a
year old.

The interesting finding is that this is **not** a "can Gleam do this" problem. Every
layer has at least one credible answer. It is a "who maintains it in three years"
problem, and it lands on one specific decision: how much of the framework's
foundation you are willing to vendor.

## Package maturity — how this was judged

Gleam is a small ecosystem, so *one maintainer is the norm and not a signal*.
Discarding that axis, what remains is:

| Axis | Why it discriminates |
|---|---|
| Release *history* vs. a single publish | A package with 11 releases has survived its own breaking changes |
| Repo reachable | Several Hex packages link to deleted repos — no issues, no forks, no upstream |
| Tests + CI in-repo | Present in most; absent in some surprising places |
| Commits spread over time | Created-and-abandoned-same-day is the dominant pattern below |
| Weekly downloads, not all-time | All-time is dominated by CI and mirror traffic |

That last one matters more than expected. `anthropic_gleam` shows **34,166 all-time
downloads but 22 in the last week**. All-time counts on Hex are close to noise for
small packages; weekly is the only honest adoption number.

## Layer by layer

### Language and runtime — solid, and very recently so
`gleam_stdlib` reached **v1.0.0 on 2026-04-18** — five months ago. Before that it
ran 0.44 → 0.71 in about seventeen months, every minor version breaking. `gleam_otp`
reached v1.0 in June 2025 and now exposes `actor`, `static_supervisor`,
`factory_supervisor` and `supervision`.

This is the single most important maturity fact in this note. The ecosystem is real
but its stability guarantee is months old, not years. Libraries written against
0.4x are still being ported.

### HTTP, web, database — production-ready
- **`wisp` 2.2.2** — 35 releases since 2023, actively maintained. Two releases were
  *retired for a path-traversal flaw in `serve_static`*, which is worth reading both
  ways: a real vulnerability shipped, and the maintainer retired the affected
  versions properly rather than quietly patching.
- **`pog` 4.1.0** — Postgres client, by Gleam's creator. No release since 2025-07-14,
  but **4,264 downloads/week**. Stable, not abandoned — an important distinction.
- **`squirrel` 4.7.0** — type-safe SQL, by a core-team member. Generates Gleam types
  from `.sql` files against a live database. Active, 42 releases.
- **`cigogne` 5.0.6** — Postgres migrations.
- **`lustre` 5.7.1** — 90 releases since 2022. Relevant to the
  [chat surface](chat-surface.md) question: its **server components** would put a
  streaming UI in the same language and process tree as the runtime.

This layer is genuinely fine. `../orkestra` runs on `wisp` + `mist` + `lustre`.

### LLM client — prefer an OpenAI-compatible client, not an Anthropic SDK
The three Gleam Anthropic SDKs are all effectively dead:

| Package | Releases | Weekly | Repo state |
|---|---|---|---|
| `anthropic_gleam` 0.1.1 | 2, both Jan 2026 | 22 | **404 — repo deleted** |
| `claude_gleam` 1.0.0 | 1 | 11 | Created and last pushed the *same minute*, 2026-02-05, 1 star |
| `catastrophic` | not on Hex | — | 4 commits, one day, 0 stars |

Going OpenAI-compatible instead is the better call, and not only because the
packages are healthier — it means Gleam needs **one client shape** rather than one
SDK per provider, and pushes provider routing, fallback and cost caps out to a model
gateway (LiteLLM/OpenRouter, still unresearched — see
[open questions](open-questions.md)). That shrinks the part of this landscape Gleam
has to cover on its own, which is exactly where it is weakest.

**`glopenai` 1.0.0** (MIT, `nilp0inter`) is the strongest candidate and is
surprisingly complete — 20 modules covering `chat`, `response`, `embedding`,
`batch`, `vector_store`, `moderation`, `file` and `upload`. It has full tool
calling on both the Chat Completions and Responses APIs (`with_tools`,
`with_tool_choice`, `ToolCall` decoders, and `McpToolCall`), and real streaming
with SSE parsing (`parse_stream_chunk`, `parse_stream_event`).

Three parts of it map straight onto the architecture sketch: `batch` is the
half-cost async path the [pipeline layer](architecture-sketch.md#6-data-pipelines)
wants, `embedding` covers [retrieval](architecture-sketch.md#7-context-and-memory),
and the streaming events feed the chat surface.

The caveat is the shape of its history: **100 commits between 2026-04-15 and
2026-04-18, then five months of silence**. It has tests and CI, an MIT licence and
0 stars. A large generated-then-abandoned client. The generated-ness is arguably
fine for an API binding — it is the OpenAPI spec rendered into types — but nobody
is maintaining it as the spec moves.

Alternatives are thinner: `gllm` (5 commits, one day), `gopenai` (no repo link,
last touched 2024), `starlet`, `starflow`.

### Tool schemas and structured output — the question the handover asked
This is where Gleam's type system either pays off or doesn't, and the answer is
**it pays off, via one of three distinct designs**:

**1. Hand-mirrored JSON Schema — doesn't pay off.** `anthropic_gleam` models schemas
as `PropertySchema(property_type: String, ...)`, a record-shaped mirror of JSON
Schema, while tool input arrives as an unparsed `String`. The schema and the decoder
are written separately and nothing checks they agree. This is the same thing
`../mcp_packages` does by hand today — its tool definitions are built from
`#("package_name", "string", "Name of the package", True)` tuples. It works, and it
is exactly the drift the [tool registry principle](../README.md#design-principles)
exists to prevent.

**2. Combined schema+decoder (`glon`).** `JsonSchema(node: SchemaNode, decoder:
Decoder(t))` — one value carrying both, "in sync by construction", composed with
Gleam's `use` syntax the same way `gleam/dynamic/decode` works:

```gleam
let schema = {
  use name <- glon.field("name", glon.string())
  use age  <- glon.field("age", glon.integer())
  glon.success(User(name:, age:))
}
```

`claude_gleam` builds its registry on this: `Tool(a)` carries `params_schema:
JsonSchema(a)` and `execute: fn(a) -> Result(String, String)`, with the registry
erasing the type parameter — precisely the heterogeneous typed registry the
architecture sketch wants.

The design is right; the package is not. **251 all-time downloads, 8/week, one
release, no repository link at all, 840 lines in a single file, and no tests in the
published tarball.** It also has **no encoder** — `to_json` serialises the *schema*,
not a value — so writing structured output back to the run store needs hand-written
encoders that nothing checks against the schema.

**3. Codegen from a spec (`castor` + `aide_generator`) — the best fit.** `aide/tool`
defines `Spec` with input and output schemas as `castor.Ref(castor.Schema)`, and
notes that the spec deliberately excludes the decoder because *"the decoders (and
encoder) are generated from this spec"*. That is principle #1 of this repo —
one typed definition, many emitted artefacts — implemented as codegen, and unlike
`glon` it generates **both** directions.

`castor` (Apache-2.0, `crowdhailer`) is the most credible schema library found:
4 releases Dec 2025 – Mar 2026, 14,802 downloads, 73/week.

### MCP servers — better than `../mcp_packages` suggests
`../mcp_packages` hand-rolls the protocol, which implies nothing existed. Something
does now:

- **`aide` 0.7.1** (Apache-2.0, `crowdhailer`) — **11 releases**, tests and CI in
  repo, `aide/definitions` carrying the full MCP schema (204 functions, 87 types),
  plus `aide/tool` and `aide/effect` for sync-or-async handlers.
- **`aide_generator` 0.4.1** — generates encoders and decoders for MCP tools.
- `mcp_toolkit` 0.3.1 — 5 releases, servers and transports.
- `mcp_client` 0.1.0 — client side, JSON-RPC over stdio.

`aide` has the most release history of anything in the agentic layer here and is
the natural base for [MCP topology](mcp-topology.md). Note it is still 0.x, and
stdio/HTTP transport support needs checking against the
[identity-in-the-transport](mcp-topology.md#identity-belongs-in-the-transport-from-day-one)
requirement before committing.

### Orchestration and durable jobs — the real gap
The architecture sketch needs a durable queue with cron, retries, backoff and
dead-lettering. Two options, both uncomfortable:

**`mule` 0.1.0** is an astonishingly complete Oban port — `engines/postgres`,
`engines/sqlite`, `plugins/cron`, `plugins/pruner`, `plugins/lifeline`,
`jobs/backoff`, `jobs/states`, `jobs/transitions`, `notifiers/postgres`
(LISTEN/NOTIFY), `telemetry`, `testing`, and a supervision tree of
foreman/stager/executor/producer/drainer. Roughly Oban's architecture module for
module, in Gleam, on Postgres — which is the deployment we already have.

And it was **published on 2026-09-23, three days ago, one release, 51 downloads, and
its GitHub repository does not exist.** It cannot be evaluated beyond its Hex
tarball. Genuinely worth watching; not something to build on this quarter.

**Or call Oban via FFI.** Confirmed possible — the Gleam docs state plainly that
*"Erlang rebar3 packages and Elixir mix packages can also be added as dependencies
without any change in syntax"*, and `../orkestra` already pulls the Erlang
`esqlite` through rebar3. So Oban, `opentelemetry`, `ex_json_schema` and the rest of
the BEAM ecosystem are reachable.

But this is the honest answer to the handover's question *"can it borrow Elixir's
Oban/Broadway, or does that break the type story?"* — **it borrows fine and the type
story stops at the boundary.** Every FFI call is a hand-written `@external`
declaration whose type signature is an assertion the compiler cannot check. Borrow
one library and that is a contained cost; borrow the queue, the scheduler and the
telemetry layer and a meaningful share of the framework's spine is untyped
hand-declared bindings — which removes the main reason to have chosen Gleam.

### Observability — OTel to Langfuse works, and nothing hands it to you
Since [Langfuse Cloud is effectively free](nonprofit-programs.md), the question is
whether a Gleam runtime can feed it. It can, over OTLP, in four pieces — none of
which is the OpenAI client.

**The client contributes nothing.** `glopenai` has *zero* telemetry surface: no
hooks, no middleware, no interceptor, not one function matching trace/span/
telemetry. Every span is opened and populated by our own wrapper around the call.
The same is true of `gllm` and the abandoned Anthropic SDKs. No Gleam LLM client
instruments itself.

**Two Gleam OTel bindings exist**, both Apache-2.0 wrappers over the Erlang
`opentelemetry` libraries:

| | Releases | Weekly | Last release | Surface |
|---|---|---|---|---|
| `opengleametry` 2.0.0 | 3 | 18 | 2026-06-06 | `span.with`, `with_links`, `set_attributes`, `set_error`, `current`, plus cross-process context for spans that continue inside an actor |
| `glotel` 1.0.1 | 3 | 12 | 2025-12-21 | `span.new`, `new_of_kind`, `set_attribute`, `set_error`, `traceparent` extraction from request headers, and `try` wrappers that mark a span failed on `Error` |

`opengleametry` is the more current and its `use_in_this_process` matters for an
agent runtime where a run's steps execute in spawned processes. `glotel`'s
`extract_values` (inbound `traceparent`) is what threads
[one trace id through everything](architecture-sketch.md#10-observability-and-ledger)
from an HTTP entry point. Taking both is reasonable; they wrap the same Erlang API.

**Langfuse accepts OTLP directly** at `/api/public/otel` (`https://cloud.langfuse.com`
for EU), over **HTTP/protobuf or HTTP/JSON — gRPC is not supported**, with Basic auth
carrying base64 `pk-lf-…:sk-lf-…`, plus `x-langfuse-ingestion-version: 4` for v4
real-time ingestion. The export itself is done by Erlang's `opentelemetry_exporter`,
configured in Erlang/OTP config rather than in Gleam.

**The attribute mapping is the part that needs care.** Langfuse reads
`langfuse.observation.*` first and falls back to `gen_ai.*`:

| Field | Attribute |
|---|---|
| Model | `langfuse.observation.model.name` → `gen_ai.request.model` |
| Input | `langfuse.observation.input` → `gen_ai.prompt` |
| Output | `langfuse.observation.output` → `gen_ai.completion` |
| Tokens | `langfuse.observation.usage_details` (JSON string) → `gen_ai.usage.*` |
| Cost | `langfuse.observation.cost_details` (JSON string) → `gen_ai.usage.cost` |

Neither Gleam package ships GenAI semantic conventions, so these are set as bare
strings — a small module of our own, not a blocker.

One constraint saves this: both bindings only accept `List(#(String, String))`,
i.e. **string-valued attributes only**, which would make the numeric `gen_ai.usage.*`
convention unreachable. The `langfuse.*` namespace takes its usage and cost as JSON
*strings*, so the preferred path is also the only expressible one.

**Two real limits.** Both bindings are marked **Erlang only**, so a Gleam MCP server
on the JavaScript target — which is exactly what `../mcp_packages` is — gets no OTel
from either. And `langfuse_client` 2.0.0 does *not* help here: despite the name it is
read-only over `score` and `metrics` with no trace or observation ingestion at all.
It is useful to the [eval harness](architecture-sketch.md#8-harness--evals) for
pulling scores back out, not for getting traces in.

Given our own run store is a design centrepiece anyway, posting to Langfuse's
ingestion API from it remains the simpler first move; OTLP is the better end state
and is genuinely available.

### Retrieval — nothing native
No Gleam pgvector binding. pgvector is a Postgres extension, so `pog` can query it
with hand-written SQL and a `vector` column cast — real work, but not blocked.

### Auth — nothing native
No Gleam OAuth or JWT library. `gleam_crypto` and `kryptos` give primitives; the
Erlang `jwerl` / `p1_oauth2` are reachable by FFI. Relevant to
[open question #4](open-questions.md#4-identity-model) and to
`../scoutid-keycloak-provider` as prior art.

### Evals and cassettes — nothing, as everywhere
No cassette/replay library in any of the three languages surveyed. Confirms this
gets written regardless of language, so it does not discriminate.

## Prior art in the user's own repos

- **`../mcp_packages`** — Gleam MCP server on Cloudflare Workers, `target =
  "javascript"`, on `gleam_json` / `gleam_http` / `gleam_fetch` / `plinth`. Proves
  Gleam-on-JS for MCP, and hand-rolls the protocol and its tool schemas.
- **`../orkestra`** — `target = "erlang"`, `wisp` + `mist` + `lustre` + `sqlight` +
  `cigogne` + `formal` + `palabres`, with a generated `sql.gleam`. This is close to
  the shape the framework's `api` and `web` apps would take.

Together these cover both targets and remove most of the "can we actually ship
Gleam" risk. Neither touches an LLM, a queue or a durable run store.

## What would have to be written

Assuming `glopenai` + `aide` + `castor` + `pog` + `squirrel`:

1. **The tool registry itself** — the metadata the sketch calls for (`read|write`,
   cost hint, idempotency, required scope, approval mode) sits above any of these.
2. **The agent loop** — `claude_gleam` has one worth reading, but it is
   Anthropic-shaped and abandoned; on an OpenAI-compatible client this is ours.
3. **Policy layer** — nothing anywhere.
4. **Run store, cassettes, evals** — ours in every language.
5. **Durable queue** — `mule`, FFI to Oban, or hand-rolled on Postgres `SKIP LOCKED`.
6. **pgvector access, OAuth** — hand-written SQL and FFI.
7. **LLM span instrumentation** — the OTel bindings give spans and attributes; the
   `langfuse.observation.*` attribute names and the wrapper that opens a span per
   model call are ours.

Items 1, 3 and 4 are ours in any language. The Gleam-specific tax is items 2, 5
and 6.

## The honest counterweight

The handover asked for this, so, plainly:

- The **LLM layer is a graveyard**. Of nine agentic packages examined, seven were
  created and abandoned inside a week. `pig` (67 commits, active this month, but no
  tests and no CI) and `aide` (11 releases, tests, CI) are the only two showing
  sustained work.
- **`gleam_stdlib` hit 1.0 five months ago.** The floor is new.
- **Vendoring is the realistic plan, not the fallback.** `glon` is 840 lines;
  `glopenai`'s used surface is a fraction of its 20 modules. Both are small enough
  to fork and own — which is a real option for a framework meant to last, and a real
  cost to state out loud rather than discover later.
- Against a framework whose value is **many integrations**, ecosystem size is the
  standing objection. Every Gmail, Calendar and Slack binding is ours to write,
  where TypeScript and Python have maintained SDKs. This is the argument that should
  decide it, and it is unchanged by anything above.

## Method, and a warning about Hex search

The `gleam_packages` MCP server searches **all of Hex** and ranks by relevance across
an ecosystem that is overwhelmingly Elixir. Searching it for "mcp" returns nine
Elixir MCP libraries and **no Gleam ones** — which is wrong. `aide`, `mcp_toolkit`
and `mcp_client` all exist. The same search pattern hid `mule` behind Oban and Exq,
and hid `opengleametry` and `glotel` behind thirty Elixir `opentelemetry_*` packages.

Each of those three gaps was reported here as "nothing exists in Gleam" before the
Gleam-only index contradicted it. The failure mode is consistent: a Gleam package
with two hundred downloads never outranks an Elixir package with thirty million, so
**absence in Hex search is not evidence of absence**.

Use **<https://packages.gleam.run>** for "does this exist in Gleam", and the
`gleam_packages` server for module and function detail once a package is known. The
first search here produced a materially wrong picture of the ecosystem, and the
correction came only from the Gleam-only index.

All download counts, release dates and repository states were read from the Hex API
and the GitHub API on 2026-09-26.

---

Next: [Language decision](language-decision.md) · [MCP topology](mcp-topology.md)
