# Research

Design notes and open-source landscape research behind
[agentic-framework](../README.md). Written September 2026; the landscape moves
fast, so treat anything here older than a few months as needing a re-check.

## Contents

### [Architecture sketch](architecture-sketch.md)
The components an agentic framework of this kind needs — tool registry,
integrations, agent runtime, policy, orchestration, pipelines, memory, harness,
surfaces, observability — and which of them carry the design. Also the additional
goals worth adopting beyond the original four, and a suggested build order.
**Read this first**; the landscape notes are organised around its layers.

### [TypeScript landscape](landscape-typescript.md)
What open source covers each layer in TypeScript, with a buy/build verdict per
layer. Two candidate stacks (thin-and-owned vs. batteries-included), the two real
gaps — approvals and batch pipelines — and why the low-code automation platforms
are the wrong shape for this.

### [Python landscape](landscape-python.md)
The same survey in Python. Richer in agent runtimes, durable execution, batch
pipelines, memory and MCP tooling; notably weaker in exactly one place — the chat
UI — which is what drags TypeScript back in regardless.

### [Language decision](language-decision.md)
The question is not Python vs. TypeScript on merit, it is one language or two.
The three options, what the polyglot tax actually costs at our size, and the
single question that decides it.

### [MCP topology](mcp-topology.md)
One MCP server per integration boundary rather than one per framework, and why:
tool-count dilution and differing auth identities. Includes the read/write split,
why policy must run server-side, and why identity has to be in the transport from
day one.

### [Chat surface](chat-surface.md)
Whether to build a chat UI or adopt [Open WebUI](https://github.com/open-webui/open-webui)
wholesale. Native Streamable-HTTP MCP support makes it fit the tool registry
directly and solves identity propagation for free; its licence, its lack of
approval gating, and the line between "a surface" and "the framework" are the
things to know before committing.

### [Open questions](open-questions.md)
Decisions still outstanding, each with the options and what hangs on them —
deployment shape, identity model, chat surface, mail trigger latency, and how
generic the framework should be.

## Sources

Primary sources (GitHub repos, official docs) are linked inline in each file. A
large share of search results in this space is SEO-generated comparison content;
claims sourced from vendor blogs comparing themselves to competitors are marked
as such where they appear.
