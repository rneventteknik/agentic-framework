# agentic-framework

A framework for building, running and supervising LLM agents against RN Eventteknik's
systems — [backstage2](https://github.com/rneventteknik/backstage2), the shared mail
inbox, the calendar, Slack — so that routine work can be automated, proposed or
answered by an agent instead of a human.

> **Status: design phase.** No code yet. The repo currently holds the architecture
> sketch and the open-source landscape research that will decide the stack.
> See **[research/](research/)**.

## Goals

- **Automate agentically.** Recurring work — triage, reconciliation, follow-ups,
  drafting — handled by agents that call typed tools against our own systems.
- **Build harnesses.** Agents are only maintainable if their behaviour can be
  measured. Every run recorded; past runs replayable against a changed prompt;
  regressions visible before they ship.
- **Chat interface.** One place to ask questions of, and give instructions to, the
  integrations — instead of clicking through four systems.
- **Data pipelines.** Run LLM jobs over many rows, on a schedule or a trigger, and
  re-run them cheaply when a prompt changes.
- **Stay safe by default.** Agents propose; humans commit. Writes are gated by an
  explicit policy layer, not by hoping the prompt holds.

## Design principles

These fall out of the research and are the load-bearing decisions so far:

1. **The tool registry is the single source of truth.** One typed definition per
   capability, emitted as Anthropic tool definitions, MCP servers and HTTP routes.
2. **Agents never write to another system's tables.** Bulk reads may go direct to
   the database; writes go through the owning system's API so its validation and
   changelog still apply.
3. **Policy sits under the registry, not above it.** Approval, spend caps and
   dry-run apply identically whether a tool is called by an agent, over HTTP, or
   from an MCP client.
4. **Content fetched by a tool is data, never instructions.** Mail bodies and
   customer text are untrusted input and cannot trigger a write on their own.
5. **Prompts and agent definitions live in git.** The database holds runs and
   outputs only.

## Research

The stack is not chosen yet. The reasoning, and the open-source landscape it is
based on, is written up in **[research/](research/README.md)** — start there.

| | |
|---|---|
| [Architecture sketch](research/architecture-sketch.md) | The components an agentic framework needs, and why |
| [TypeScript landscape](research/landscape-typescript.md) | What open source covers, per layer, in TS |
| [Python landscape](research/landscape-python.md) | The same, in Python |
| [Language decision](research/language-decision.md) | One language or two — the actual trade-off |
| [MCP topology](research/mcp-topology.md) | How the tool registry is split into MCP servers |
| [Open questions](research/open-questions.md) | Decisions still to make |
