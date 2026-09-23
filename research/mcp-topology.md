# MCP topology

[← Research index](README.md)

How the [tool registry](architecture-sketch.md#1-tool-registry) gets exposed over
MCP. Settled: **one server per integration boundary**, not one per framework and
not one giant server.

## Why not one server

1. **Tool-count dilution.** Past roughly 30–40 tools in a single server, model
   accuracy in picking the right one degrades noticeably — and every tool
   definition is paid for in every request's context whether relevant or not. A
   registry covering mail + calendar + backstage + Slack + pipelines + run
   introspection passes that ceiling quickly.
2. **Different trust and auth boundaries.** Mail tools act as a mailbox identity,
   backstage tools as an API-key identity, run-store tools as an operator.
   Collapsing them means one connection grants all of it, and the ability to hand
   a narrow surface to a narrow agent is lost.

## The split

By integration domain, one server per integration package:

```
packages/integrations/mail/      → mcp: rn-mail
packages/integrations/calendar/  → mcp: rn-calendar
packages/integrations/backstage/ → mcp: rn-backstage
packages/integrations/slack/     → mcp: rn-slack
packages/core/                   → mcp: rn-runs      (read: runs, traces, agents)
                                 → mcp: rn-pipelines (write: trigger, cancel, backfill)
```

Each is a thin generated shim over the same registry — filter by package, emit.
The registry stays the single source of truth; MCP is one of its output formats
alongside Anthropic tool definitions and HTTP routes.

**Ops is split in two deliberately.** Run and trace introspection is read-only
over our own data and is the surface we will use constantly from Claude Code.
Pipeline control — trigger, cancel, backfill — is a real write surface with real
blast radius. The trust gap *inside* ops is wider than the gap inside mail, which
is the one place a strict by-integration rule undersells the split.

## Why this matters beyond hygiene

It makes the tool subset in an agent definition and the MCP server list **the same
concept**. A mail-triage agent gets `[rn-mail, rn-backstage]`; in Claude Code,
exactly those two get enabled. The scoping designed for agents applies verbatim to
ourselves.

## Three things to build in from the start

### Read-only is a property of the registry, not a server flag
Tools declare `read | write`. A server started without an explicit write grant
simply does not emit the write ones. Then "read-only MCP for Claude Code" and
"this agent may only read" are the same mechanism rather than two parallel ones —
and there is no shim-level filter to forget. The read-only configuration is the
one in use ~90% of the time, so it should be one flag rather than a hand-curated
allowlist.

### Policy runs server-side, under the registry
The approval, spend-cap and dry-run layer sits beneath the registry so it applies
identically whether a tool is invoked by an agent run, an HTTP call or an MCP
client. Otherwise the MCP surface becomes the hole in the policy layer — tools
called from Claude Code bypassing the approval rules the same tools obey inside an
agent run.

### Identity belongs in the transport from day one
Policy under the registry is only half of it: *"approved by whom"* is unanswerable
unless the MCP client's identity propagates into the policy layer. A shared bearer
token produces an audit log that says "someone". That argues for per-connection
identity immediately — which is what the MCP 2026-07-28 revision's OAuth alignment
and RFC 8707 audience validation exist for. **Retrofitting identity is worse than
retrofitting transport.**

Worth knowing that [Open WebUI](chat-surface.md), if adopted as the chat surface,
supplies this directly: OAuth 2.1 or bearer auth plus custom headers templated
with `{{USER_ID}}` / `{{USER_EMAIL}}` / `{{USER_ROLE}}`, so the human's identity
reaches the policy layer without an identity broker of our own.

## Transport

HTTP (Streamable HTTP) first, with stdio as a local-dev convenience wrapper. stdio
is trivial locally but awkward for anything hosted, and these servers need to be
reachable from a deployed chat backend too. Retrofitting in that direction is more
annoying than starting there. Cheap in both SDKs, and close to free with
[FastMCP](https://gofastmcp.com/getting-started/welcome) if the stack ends up
Python.

---

Next: [Open questions](open-questions.md)
