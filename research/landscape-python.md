# Open-source landscape — Python

[← Research index](README.md) · Surveyed September 2026

The same survey as the [TypeScript landscape](landscape-typescript.md), in Python.

## Headline

Richer than TypeScript in three layers, roughly equal in two, and worse in exactly
one — and the one it is worse at is the one that drags a second language back in.

## Agent runtime — deeper bench, same conclusion

[LangGraph](https://www.langchain.com/resources/ai-agent-frameworks) since 1.0 has
focused on precisely our production concerns: durable execution that resumes where
it left off, human-in-the-loop interrupts, short- and long-term memory, with a
Postgres checkpointer. It is the closest thing to "the approval gap is already
solved for me."

[PydanticAI](https://ai.pydantic.dev) is the thin, typed option — the Python
analogue of AI SDK 6, though less proven at scale. The OpenAI Agents SDK (~19k★)
is minimal with HITL built in. Claude Agent SDK, Google ADK and Strands all have
Python parity or are Python-first.

**Net: more mature options, but this layer was never going to be the loser in
either language.**

## Batch pipelines — the decisive advantage

The one place the gap is large. The requirement from the architecture sketch —
content-hash each row against the prompt version, reprocess only what changed,
diff two pipeline versions, backfill cheaply — is literally
[Dagster](https://dagster.io/guides/data-pipelines-with-python-6-frameworks-quick-tutorial)'s
partitioned-asset model with asset checks, or Prefect's `@materialize` asset
layer. Airflow ships LLM operators now as well.

In TypeScript this gets built. In Python it gets configured, and lineage,
backfills and a UI come with it. Behind it sits the whole data stack — Polars,
DuckDB, Daft, Arrow — which has no real TypeScript equivalent.

## Durable execution — also better

[DBOS](https://tiarebalbi.com/en/blog/dbos-vs-temporal-postgres-durable-execution)
anchors durability directly in Postgres, on the thesis that the database already
solves durability, concurrency and state. [Hatchet](https://github.com/hatchet-dev/hatchet)
is a Postgres-backed durable task queue with DAG dependencies, retries, concurrency
keys and good run observability. `procrastinate` is the lightweight Postgres
option.

All three fit "one Heroku Postgres, no Redis" better than anything comparable in
TypeScript.

## MCP — meaningfully nicer

[FastMCP](https://gofastmcp.com/getting-started/welcome) reached v4.0.0 in August
2026 and reportedly powers around 70% of MCP servers across all languages.
Decorator-based schema derivation, server composition and mounting, Streamable
HTTP as the production transport, RFC 8707 audience validation for OAuth.

Generating N servers from one registry is closer to free here than with the
TypeScript SDK — directly relevant given the [MCP topology](mcp-topology.md) we
want.

## Evals and memory — modest edge

DeepEval is [pytest-for-LLM-outputs](https://deepeval.com/blog/top-5-llm-evaluation-frameworks),
which makes "evals run in CI" a non-event. Ragas covers retrieval quality.
promptfoo is a CLI, so it works regardless of implementation language.

Memory is Python-first across the board — [Letta](https://vectorize.io/articles/best-ai-agent-memory-systems)
(Postgres + pgvector, agent-scoped, fully self-hostable), Mem0, Graphiti — with
TypeScript ports lagging. Note that Zep retired its self-hosted community edition.

## Observability — a wash

Langfuse has a first-class Python SDK either way. Phoenix is Python-native
(ELv2). [Logfire](https://github.com/pydantic/logfire)'s SDKs are MIT and
OTel-native, but the backend is closed and self-hosting requires an enterprise
licence — the OTel-native part means it can export to any backend, which softens
that.

## Chat UI — the weak spot

Chainlit is the obvious Python pick, but the founding team
[stepped back in May 2025](https://www.innonexa.com/2026/07/02/streamlit-alternatives-python-ai-agent-apps-2026/)
and it is community-maintained now, with two high-severity CVEs reported late in
2025. Streamlit's rerun model fights the chat pattern; Gradio is demo-grade.

One practical answer is to keep the UI in TypeScript (assistant-ui or CopilotKit)
and talk to a Python backend over [AG-UI](https://docs.ag-ui.com/introduction) —
which works fine; the protocol is language-agnostic with 40+ integrations. But
that means Python does not buy one language, it buys Python plus a TypeScript
frontend.

The better answer is probably not to build a chat UI at all.
[Open WebUI](chat-surface.md) is a finished self-hosted chat product with native
Streamable-HTTP MCP support, which turns this layer from a build into a
configuration — and largely dissolves the objection above. See
[chat surface](chat-surface.md).

---

Next: [Language decision](language-decision.md)
