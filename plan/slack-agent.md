# Slack agent, then a LiteLLM gateway

The goal is a first slice that runs: someone asks a question in Slack, and the
agent answers it using the backstage2 MCP server (`search_bookings`,
`get_booking`). It runs on our Proxmox host and is deployed from this repo.

The work is in two parts:

1. **[MVP](#part-1-mvp)**: a Pydantic AI agent in Slack that calls the Anthropic
   API and the backstage2 MCP server directly.
2. **[LiteLLM gateway](#part-2-litellm-gateway)**: once the MVP runs, put a
   self-hosted LiteLLM between the agent and both of those, for keys, budgets and
   reuse by other clients.

The slice is deliberately small. The agent is Python because Pydantic AI is, but
that does not settle the framework's language
([open question #1](../research/open-questions.md)); the agent is small enough to
rewrite. What it does settle is how we host and deploy things, plus a first answer
to [open question #5](../research/open-questions.md#5-chat-surface-first--slack-or-web):
Slack comes first.

## Constraints

- **The hardware is on the local network.** No ports are opened to the internet,
  and nothing is exposed through a tunnel. Admin interfaces are reachable from the
  local network only.
- **This repo is public.** Anything committed can be read by anyone, and pull
  requests can come from forks. Two things follow: secrets are never committed in
  plain text, and no CI job ever runs on our network.
- **Use prebuilt images where they exist.** Images we build ourselves are built
  by GitHub Actions and published to GHCR.

# Part 1: MVP

## Architecture

```
                      ┌──────────── Proxmox VM ────────────┐
  Slack  ◀── WSS ─────┤ stagehand-qvack (Pydantic AI)      │
  (Socket Mode)       │ doco-cd                            │
                      └──┬─────────┬──────────┬────────┬───┘
                         │         │          │        │
                    polls repo  pulls images  │        │
                         ▼         ▼          ▼        ▼
                      GitHub     GHCR    Anthropic   backstage2 MCP
                                         API         on Heroku
```

Every arrow starts inside the VM, so nothing on the local network accepts an
inbound connection:

- **The Slack agent uses Socket Mode.** It opens an outbound WebSocket to Slack,
  so Slack never needs a public URL to deliver events.
- **The agent calls Anthropic and backstage2 directly.** backstage2 runs on
  Heroku and is reachable over the internet. Its `/api/mcp` serves both current
  and 2025-era MCP clients statelessly, so the Python MCP SDK that Pydantic AI
  uses can connect to it.
- **The VM pulls its own deployments.** See [Deployment](#deployment).

## Repository layout

```
infra/
  proxmox/            OpenTofu: the VM, its cloud image and cloud-init
deploy/
  compose.yml         the stack: stagehand-qvack from its GHCR image, with its
                      secrets passed in from the environment
  compose.local.yml   override for a laptop: builds stagehand-qvack from source
  secrets.enc.env     SOPS-encrypted environment for the stack
  .sops.yaml          age recipients
.doco-cd.yml          what doco-cd deploys from this repo
stagehand-qvack/      Slack CLI project: manifest, Bolt + Pydantic AI app, Dockerfile
  .env.sample         the variables the agent needs; .env itself is gitignored
.github/workflows/
  stagehand-qvack.yml test, build, push to ghcr.io/rneventteknik/stagehand-qvack
renovate.json
```

## Infrastructure as code

**OpenTofu** with the `bpg/proxmox` provider. It downloads the Debian cloud image
and creates the VM (CPU, memory, disk, network), with a cloud-init snippet that
installs Docker, writes the age key, and starts doco-cd.

- **Tofu runs from a laptop on the LAN,** not from CI. The VM changes rarely, and
  running it from CI would mean either giving CI a route into the network or
  putting a runner inside it (see [Security](#security)).
- **State goes in a Cloudflare R2 bucket** through the S3 backend, with OpenTofu's
  state encryption enabled. State is never committed.
- **The Proxmox API token** is scoped to one pool, kept in the password manager
  and exported locally. It never goes into the repo or into GitHub secrets.
- **Use a VM, not an LXC container.** Docker in an unprivileged LXC works but
  breaks often enough to cost more than the VM's overhead.

The Slack app is configured as code too, with the Slack CLI. See
[Slack agent](#slack-agent).

## Deployment

The VM **pulls** its deployments. Nothing pushes to it.

- **doco-cd** runs on the VM, polls this repo's `main` branch, and runs
  `docker compose up` on `deploy/compose.yml` when it changes. Merging to `main` is
  the deploy. Polling every minute or so is fast enough and needs no webhook,
  which would need an inbound route.
- **doco-cd is not part of `compose.yml`.** cloud-init starts it on the VM as its
  own container, so `compose.yml` holds only the stack and runs unchanged on a
  laptop with `compose.local.yml` on top.
- **Secrets** are kept in `deploy/secrets.enc.env`, encrypted with SOPS for an age
  key. The age private key exists only on the VM (written by cloud-init) and in the
  password manager. doco-cd decrypts the file at deploy time.
- **Every image is pinned by digest.** Renovate opens PRs that bump the digests.
  A merged bump is deployed by the poll like any other change.

**GitHub Actions only builds.** The `stagehand-qvack` workflow runs on GitHub-hosted
runners when `stagehand-qvack/` changes. It tests the agent, builds the image, and
pushes it to GHCR as `ghcr.io/rneventteknik/stagehand-qvack`, tagged with the commit
SHA. A follow-up commit, from Renovate or by hand, moves the digest in
`compose.yml`.

## Credentials

- **Anthropic:** an API key from a dedicated Anthropic Console workspace with a
  monthly spend limit. Until LiteLLM is in place, that limit is the budget.
- **backstage2:** add a key named `stagehand-qvack` to `MCP_API_KEYS` on Heroku.
  **Leave out the `pii` scope.** Answers are posted in Slack, where more people can
  read them than have access to backstage2, so full names and customer contact
  details should not come back by default. Add the scope later, and only if the
  agent's audience is limited to people who already have that access in
  backstage2.
- **Slack:** the bot token, and an app-level token with `connections:write` for
  Socket Mode.

`deploy/compose.yml` lists them by name only, so their values come from
whatever runs Compose. On the VM, they go into `deploy/secrets.enc.env`. On a
laptop, they go into `stagehand-qvack/.env`, which is gitignored, uses the
development app's Slack tokens, and is passed with `--env-file`.

## Slack agent

The agent is a Slack app with the **Agents** feature enabled, so it gets its own
entry point in Slack's top bar, a side panel next to whatever the user is viewing,
and a Messages tab. See Slack's
[developing agents](https://docs.slack.dev/ai/developing-agents) guide. It also
answers @mentions in channels.

### Created and configured with the Slack CLI

All of it lives in `stagehand-qvack/`:

- **Create** the project with `slack create`, from the Bolt for Python template in
  Slack's [agent quickstart](https://docs.slack.dev/ai/agent-quickstart). Agent
  features need at least Bolt for Python 1.29.0 and the Python Slack SDK 3.43.0
  ([changelog](https://docs.slack.dev/changelog/2026/06/30/agent-messages-tab)).
- **The manifest is the source of truth.** `stagehand-qvack/manifest.json` holds the
  name, scopes, events, Socket Mode and the agent settings, and is reviewed in PRs
  like any other code. The project's config sets the manifest source to the local
  file, so `slack install` pushes it to Slack's app settings rather than the other
  way round.
- **Two apps.** `slack run` runs a separate development app against a developer's
  workspace, with its own tokens. `slack install` installs the production app in
  RN's workspace; that is the app the container runs as. Commit the files the
  template does not ignore under `.slack/` (app IDs are not secret); never commit
  tokens.
- **The Dockerfile** lives in `stagehand-qvack/` and builds the same app for the
  container.

### Manifest settings

Slack reworked agents in mid-2026
([changelog](https://docs.slack.dev/changelog/2026/06/30/agent-messages-tab)).
Use the current `agent_view` version, not the older `assistant_view` version, the
`Assistant` class, or the `assistant_thread_started` event, which still appear in
older examples.

- `features.agent_view` with an `agent_description` and `suggested_prompts`, such
  as "What's booked next week?" ([manifest reference](https://docs.slack.dev/reference/app-manifest)).
  Switching an app from `assistant_view` to `agent_view` cannot be undone.
- `settings.socket_mode_enabled: true`.
- **Scopes:** `assistant:write`, `chat:write`, `app_mentions:read`,
  `im:history`, `channels:history` (for reading threads).
- **Events:** `message.im`, `app_mention`, `app_home_opened` (the Messages tab),
  `agent_session_stopped` (the stop button) and `agent_session_title_changed`.

### The agent

Bolt's async app (`AsyncApp` with the async Socket Mode handler) receives events,
and a Pydantic AI `Agent` answers them:

- **Model:** Anthropic, for example `anthropic:claude-sonnet-5-5`.
- **Tools:** the backstage2 MCP server as a toolset, using Pydantic AI's
  Streamable HTTP MCP client with the key in an `Authorization: Bearer` header.
  Pydantic AI lists the tools and runs the tool loop, so a question that needs
  `search_bookings` followed by `get_booking` works without extra code.
- **A cap on the loop:** Pydantic AI's usage limits, at about 6 model requests
  per message. If the cap is reached, the agent says so rather than guess.
- **The system prompt** lives in the repo (principle 5). It tells the model it
  answers questions about RN's bookings, that tool results are data and never
  instructions (principle 4), and to say so when it cannot find something rather
  than guess.

**Per message:**

1. Fetch the thread with `conversations.replies` and convert it to Pydantic AI
   message history. The agent stores no conversation state of its own.
2. Set the session status to processing (`agents.sessions.setStatus`), which shows
   a loading indicator and a stop button.
3. Run the agent and stream its answer into the thread (`chat.startStream`,
   `appendStream`, `stopStream`), with links to bookings when the tools return
   them, and feedback buttons under it.
4. If the user presses stop (`agent_session_stopped`), cancel the run.

**Recording runs.** Pydantic AI emits OpenTelemetry traces covering every model
call and tool call. Sending them to Langfuse Cloud, which
[is already the plan](../research/open-questions.md#8-observability-self-host-or-hosted),
is a few lines of configuration and worth doing from the start.

**Dependencies are locked,** including the ones we do not list ourselves. Use a
lock file (such as `uv.lock`) and install from it in the Dockerfile and in CI, so
an upstream release cannot change what runs between two builds of the same
commit. Renovate proposes upgrades as PRs, which CI tests. The next section shows
why.

### Known issue: `'typing.Union' object is not callable`

Seen in a local test setup with pydantic-ai 2.55.0. Every mention of the bot was
answered with ":warning: Something went wrong! ('typing.Union' object is not
callable)", and the traceback ended in Pydantic AI's Anthropic model:

```
File ".../pydantic_ai/models/anthropic.py", line 2450, in _map_message
    anthropic_messages.append(BetaMessageParam(role='user', content=user_content_params))
TypeError: 'typing.Union' object is not callable
```

- **Cause:** pydantic-ai 2.55.0 only sets a lower bound on the Anthropic SDK
  (`anthropic>=1.12.1`), so a fresh install gets anthropic 2.x. There,
  `BetaMessageParam` is a `Union` type alias rather than a TypedDict, and
  pydantic-ai 2.55.0 calls it as a constructor.
- **Requirement:** with anthropic 2.x, use pydantic-ai 2.64.0 or later, which does
  not call `BetaMessageParam(...)`. `pyproject.toml` depends on
  `pydantic-ai[openai,anthropic]==2.64.0`, tested against anthropic 2.3.0.
- **Fallback:** if pydantic-ai has to stay below 2.64.0, pin `anthropic` below
  2.0.

If an agent request fails with a `TypeError` inside `pydantic_ai/models/`, check
first whether the installed `anthropic` or `openai` version is newer than the
pydantic-ai release supports.

## Security

- **No self-hosted GitHub Actions runner.** On a public repo, a fork's pull
  request can end up running code on a self-hosted runner, which here would sit
  inside the LAN next to the Proxmox API. GitHub's own docs advise against it.
  The pull model above exists to avoid needing a runner.
- **Isolate the VM on the network.** Put it on its own VLAN or behind Proxmox
  firewall rules: it may make outbound HTTPS connections and accept SSH from the
  admin subnet, and nothing else. In part 2, it also accepts the LiteLLM port from
  the admin subnet. It does not need to reach the Proxmox host or other machines
  on the LAN.
- **Least-privilege tokens.** The Proxmox token is limited to the VM's pool. The
  Anthropic key belongs to a workspace with a spend limit. The backstage2 key has
  no `pii` scope.
- **Identity.** The agent calls backstage2 as a single service identity, so a
  Slack user sees whatever that key can see. This is fine for read-only booking
  data without `pii`. It is the concrete case for
  [open question #4](../research/open-questions.md), and it has to be answered
  before the agent gets write tools or personal data.

## Steps

Each step ends with a check that shows it works before the next one starts.

1. **The agent in Docker Compose on a laptop.** Needs an Anthropic workspace and
   API key, a backstage2 MCP key, and the Slack CLI logged in to RN's workspace.
   `slack create` in `stagehand-qvack/`, then the manifest, the Pydantic AI agent, the
   Dockerfile with the locked dependencies, `deploy/compose.yml` and
   `deploy/compose.local.yml`. Fill `stagehand-qvack/.env` from `.env.sample` with
   the development app's tokens, and run:

   ```sh
   docker compose -f deploy/compose.yml -f deploy/compose.local.yml \
     --env-file stagehand-qvack/.env up --build
   ```

   `slack run` is still useful for quick iteration, but the check runs against
   the container.
   *Check:* the agent entry point appears in Slack's top bar. That confirms
   agents work on our Pro plan: Slack's pricing page lists "AI assistant apps" on
   paid plans, but the developer docs only say "some AI features require a paid
   plan", and the settings are visible on every plan. In the side panel, "what
   equipment is on the next gig?" gets a correct answer, which needs
   `search_bookings` followed by `get_booking`. The same works as an @mention in a
   test channel. The trace shows both tool calls. After
   `docker compose down` and `up` again, it still works, since the agent keeps no
   state of its own.
2. **The image in GHCR.** The `stagehand-qvack` workflow, and the image digest in
   `compose.yml`.
   *Check:* the workflow publishes the image on a merge to `main`. On the laptop,
   `docker compose -f deploy/compose.yml --env-file stagehand-qvack/.env up`,
   without the local override, pulls that image and passes the step 1 check.
3. **The VM.** Needs a Proxmox API token, an R2 bucket for state and an age key
   pair. `infra/proxmox` creates the VM with cloud-init, which starts doco-cd.
   *Check:* `tofu init` succeeds against the R2 backend. SSH in from the admin
   subnet. `docker info` works. An outbound `curl https://github.com` works, and
   the VM cannot reach the Proxmox web UI.
4. **The agent, deployed.** `slack install` the production app, and put its
   tokens and the other credentials in `deploy/secrets.enc.env`. Point doco-cd at
   the repo.
   *Check:* the step 1 question works against the production app, with no
   developer machine running. A change merged to `compose.yml` is redeployed
   without touching the VM.
5. **Upkeep.** Add Renovate.
   *Check:* Renovate opens a digest bump, and merging it redeploys.

# Part 2: LiteLLM gateway

Started once the MVP has been running and used. The agent keeps its code; only
where it sends model and tool calls changes.

## What it adds

- **One place for credentials.** The Anthropic key and the backstage2 MCP key move
  into LiteLLM. The agent holds only a LiteLLM virtual key.
- **Budgets and access per client.** Each virtual key has its own budget, its own
  models and its own MCP servers. The Anthropic workspace limit becomes a
  backstop.
- **Reuse.** Any later client, such as Open WebUI
  ([chat surface](../research/chat-surface.md)), gets the same models and tools
  from the same gateway.
- **Switching models** without changing the agent.

## How the agent uses it

One LiteLLM instance serves both models and tools:

- **Models:** the agent uses an OpenAI-compatible model in Pydantic AI, pointed
  at LiteLLM's `/v1/chat/completions` with its virtual key.
- **Tools:** the agent's MCP toolset points at LiteLLM's `/mcp` endpoint instead
  of backstage2, with its virtual key in the `x-litellm-api-key` header and
  `x-mcp-servers: backstage2`. LiteLLM forwards tool calls to backstage2 with the
  key from its own config. Tool names gain the server name as a prefix, such as
  `backstage2-search_bookings`.

Pydantic AI keeps running the tool loop. LiteLLM can also run tools itself, given
an MCP tool with `require_approval: "never"` in the request
([MCP usage](https://docs.litellm.ai/docs/mcp_usage)), but we do not use that.
Its source (v1.106.6, in `litellm/responses/main.py`) makes one model call, runs
the tool calls from that response, makes a second model call with the results,
and returns. If the model asks for another tool in the second response, LiteLLM
does not run it, and most booking questions need two rounds. Keeping the loop in
the agent also keeps every step visible to us, which is principle 3 ("policy sits
under the registry") from the [README](../README.md).

## Stack additions

- **LiteLLM:** `ghcr.io/berriai/litellm-database` at a pinned release. This
  variant is needed for virtual keys, budgets and spend tracking.
- **Postgres:** a `postgres` container with a named volume, included in Proxmox's
  VM backups.
- **Keys:** the master key is used only by humans, through the admin UI. The
  agent gets a virtual key with a monthly budget, the models it needs, and the
  `backstage2` MCP server only (`object_permission`, see
  [MCP access control](https://docs.litellm.ai/docs/mcp_control)).
- **backstage2:** a new `MCP_API_KEYS` entry named `litellm`, without `pii`. The
  `stagehand-qvack` key is removed once the agent has switched over.
- **Admin UI:** served on LiteLLM's port, reachable from the admin subnet only.
  The agent reaches LiteLLM over the Compose network.

A starting `deploy/litellm/config.yaml`. The `mcp_servers` fields follow
LiteLLM's [MCP config reference](https://docs.litellm.ai/docs/mcp_config_reference);
check them against the pinned release.

```yaml
model_list:
  - model_name: claude-sonnet
    litellm_params:
      model: anthropic/claude-sonnet-5-5
      api_key: os.environ/ANTHROPIC_API_KEY

mcp_servers:
  backstage2:
    url: https://<backstage2-host>/api/mcp
    transport: http
    auth_type: bearer_token
    auth_value: os.environ/BACKSTAGE2_MCP_KEY

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  database_url: os.environ/DATABASE_URL
```

## Steps

1. **LiteLLM.** Add LiteLLM, Postgres and the config to `compose.yml`, and create
   the agent's virtual key.
   *Check:* the admin UI loads from the admin subnet and not from elsewhere on
   the LAN. From the admin subnet, with the agent's key, a chat completion against
   `claude-sonnet` succeeds. An MCP client pointed at `/mcp` lists exactly the two
   backstage2 tools and can call `backstage2-search_bookings`.
2. **Switch the agent.** Point its model and MCP toolset at LiteLLM, and remove
   the Anthropic and backstage2 keys from its environment.
   *Check:* the MVP's question still gets a correct answer, and the spend appears
   against the agent's key in LiteLLM.
3. **Backups.** Include the Postgres volume in Proxmox backups.
   *Check:* a backup can be restored to a scratch VM.

# Decisions still open

- **Who can use the agent and in which channels.** This decides whether the `pii`
  scope can ever be added.
- **Whether Open WebUI joins the stack** in part 2, as a second client of the
  gateway. It would cost one more service and give a web chat for building and
  debugging.
