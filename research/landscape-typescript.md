# Open-source landscape — TypeScript

[← Research index](README.md) · Surveyed September 2026

Mapped against the layers in the [architecture sketch](architecture-sketch.md).

## Headline

Nobody ships the whole thing. **Runtime, observability and evals are crowded and
mature; policy/approvals and batch LLM pipelines in TypeScript are genuinely
thin.**

## Per layer

| Layer | Best open-source options | Verdict |
|---|---|---|
| Agent runtime | [Mastra](https://github.com/mastra-ai/mastra) (Apache-2.0 core, ~28k★), [AI SDK 6](https://vercel.com/blog/ai-sdk-6), LangGraph.js, [Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk/typescript), [Inngest AgentKit](https://github.com/inngest/agent-kit), VoltAgent | **Adopt.** No reason to write a tool-use loop in 2026 |
| Orchestration / durability | Inngest, [Trigger.dev](https://trigger.dev), Temporal, Restate, DBOS; or [pg-boss](https://github.com/timgit/pg-boss) / [graphile-worker](https://worker.graphile.org/) | **Adopt**, sized to us |
| Tool registry / integrations | [Nango](https://nango.dev) (ELv2, self-hostable), Composio, Arcade; MCP as the de-facto format | **Mostly build**, adopt the *format* |
| Observability / run store | [Langfuse](https://github.com/langfuse/langfuse) (MIT core, ~35k★), Arize Phoenix (ELv2), Laminar (Apache-2.0), OpenLLMetry | **Adopt** — but read the self-host cost |
| Evals / harness | [promptfoo](https://promptfoo.dev) (MIT), Langfuse datasets, DeepEval, Opik | **Adopt** |
| Memory | pgvector, Letta, Mem0, Graphiti | **Adopt the boring one** (pgvector) |
| Chat UI | [assistant-ui](https://github.com/assistant-ui/assistant-ui), [CopilotKit](https://github.com/copilotkit/copilotkit) + [AG-UI](https://docs.ag-ui.com/introduction), AI Elements, LibreChat | **Adopt** |
| Policy / approvals | *gap* — only framework primitives | **Build** |
| Batch LLM pipelines | *gap* — Ray Data LLM is Python and GPU-shaped | **Build (small)** |

## Notes on the layers that matter

### Runtime — the real fork

[Mastra](https://github.com/mastra-ai/mastra) bundles roughly 70% of the
architecture sketch into one dependency: agents, graph workflows, memory, evals,
observability, MCP as both client and server, and suspend/resume for human
approval. Apache-2.0 core with enterprise features fenced into `ee/`. The cost is
buying into their abstractions throughout.

[AI SDK 6](https://vercel.com/blog/ai-sdk-6) went GA with `Agent` / `ToolLoopAgent`
as a first-class abstraction, tool-execution approval, MCP support, stop
conditions and step-level observability — and stays deliberately thin. More
control, more glue code.

The [Claude Agent SDK](https://docs.claude.com/en/api/agent-sdk/typescript) is a
different shape again: it hands over Claude Code's own loop and context
management. Right for *harness*-style agents that touch a filesystem or run code,
less so for "call my five typed tools."

**Read:** AI SDK 6 if the framework should stay out of the way; Mastra to skip
building four layers. LangGraph.js only for genuinely complex graph control flow.

### Durable execution changed the design space

The biggest recent shift. Journaling every step so an agent survives a crash,
pauses for days awaiting approval and resumes with the same tool-call history is
now table stakes — AWS, Cloudflare and Vercel all shipped durable primitives in
the past year. That directly solves the approval-resume problem.

But Temporal and Restate are heavy at our scale, and
[Inngest prices per durable step](https://www.inngest.com/blog/durable-execution-key-to-harnessing-ai-agents),
which agent loops generate a great many of. For a Heroku-sized deployment,
**pg-boss on the existing Postgres** plus the runtime's own suspend/resume is the
honest answer; graduate to Inngest or Trigger.dev when the pain is real.

### Observability has a self-hosting trap

[Langfuse](https://github.com/langfuse/langfuse) is the merit pick — MIT core with
genuinely everything in the open-source build (tracing, prompt management,
LLM-as-judge, datasets, playground). But self-hosting wants **ClickHouse +
Postgres + Redis**, a serious footprint next to a single Heroku Postgres. Options:
Langfuse Cloud with self-host as the exit, or Laminar (Apache-2.0, lighter,
OTel-native).

Either way, **still build the run store.** Langfuse is for debugging traces, not
for the domain-level audit log of "agent sent mail X, approved by Y".

### Evals — just use promptfoo

MIT, YAML-defined cases with pass/fail assertions, side-by-side model comparison,
CI regression baselines, very widely used. OpenAI
[acquired it in March 2026](https://openai.com/index/openai-to-acquire-promptfoo/)
and committed to keeping it open source under the current licence — a note for the
risk column, not a reason to avoid it. It does **not** provide cassette replay of
real tool calls; that piece stays ours.

### The approval gap is real

HumanLayer was the product for this and **pivoted away** —
[humanlayer.dev](https://www.humanlayer.dev/) now sells an AI coding IDE and the
approvals API is gone from the site. There is no drop-in replacement. What exists
is primitives: Mastra's suspend/resume, AI SDK 6's tool approval, LangGraph
interrupts, OpenAI Agents SDK's HITL flow.

Fine — policy is a few hundred lines, and it is exactly where our domain rules
live.

### Batch pipelines — nothing fits

The open-source batch-inference world ([Ray Data + vLLM](https://docs.ray.io/en/latest/data/working-with-llms.html))
is Python, GPU-cluster-shaped, and solves a problem we do not have. What we want
is fan-out over a durable queue into the Anthropic Batches API with content-hash
caching — a small custom layer on top of pg-boss, worth keeping small rather than
reaching for a platform.

### Integrations — adopt the format, not the platform

Composio, Arcade and Nango all have a closed core somewhere: the SDKs are open,
the credential-holding runtime generally is not. Nango's ELv2 self-host is the
most open of the three, though that comparison comes from
[Nango's own blog](https://nango.dev/blog/best-open-source-api-integration-platforms-for-ai-agents/)
and is worth verifying independently.

More to the point, these exist to connect to *hundreds* of SaaS apps. We have four
integrations, one of which is our own system nobody else can connect to. Write
typed tools, expose them over MCP, done.

## Two candidate stacks

**A. Thin and owned** — AI SDK 6 · pg-boss · own run store and policy · pgvector ·
promptfoo · MCP SDK · assistant-ui.
More code, no framework lock-in, every layer comprehensible. Roughly 2–3 weeks to
a working spine.

**B. Batteries included** — Mastra (runtime, workflows, memory, suspend/resume,
MCP server) · pg-boss or Mastra workflows · Langfuse Cloud · promptfoo ·
CopilotKit/AG-UI.
Days to a working spine, but their model of the world is inherited, and the policy
layer and pipeline DSL are still ours to write.

**Lean:** A, with Mastra kept as a live option. Our integration surface is small
and idiosyncratic, which is precisely where a batteries-included framework earns
least.

## What to skip

n8n, Dify, Activepieces, Windmill, Langflow. Excellent at what they do, but they
are *workflow platforms*: agents get built in a GUI, prompts do not live in git,
and evals and replay get awkward. We want a framework and we have engineers.

Also worth noting that
[n8n's licence is not OSI open source](https://www.booleanbeyond.com/insights/n8n-vs-activepieces-vs-windmill-open-source-automation)
— it is a fair-code Sustainable Use Licence — which matters if this is ever shared
outside the organisation.

---

Next: [Python landscape](landscape-python.md) · [Language decision](language-decision.md)
