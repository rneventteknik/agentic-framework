# Deploy TODO: a Portainer stack on docker-host

The fastest way to get the agent running for real: as a stack in the Portainer
that already runs on `docker-host` (10.0.3.30), a VM on our Proxmox host. It
skips the dedicated VM, OpenTofu, SOPS and doco-cd from
[the plan](slack-agent.md#deployment). See [Later](#later) for what can replace
the manual steps.

The agent fits this host well:

- **No ports and no proxy host.** It only makes outbound connections: Slack over
  Socket Mode, Anthropic, and backstage2 on Heroku. Nothing in Nginx Proxy
  Manager changes.
- **No build on the host.** GitHub Actions publishes the image to
  `ghcr.io/rneventteknik/stagehand-qvack`, which is public, so Portainer pulls it
  without registry credentials. Portainer runs its own Compose, so the host's
  Compose v1 does not matter.
- **Secrets stay out of git.** They are stack environment variables in
  Portainer.

Placeholders are in `<angle brackets>`.

## 1. Production credentials

- [ ] **Slack production app.** Install it with
  `cd stagehand-qvack && slack app install --environment deployed`, then get its
  two tokens from `slack app settings` (pick "Stagehand Qvack", not the local
  app):
  - **Bot token** (`xoxb-...`): OAuth & Permissions, Bot User OAuth Token.
  - **App-level token** (`xapp-...`): Basic Information, App-Level Tokens, with
    the `connections:write` scope only.
- [ ] **Anthropic key** from a dedicated workspace in the Anthropic Console with a
  monthly spend limit. Until LiteLLM is in place, that limit is the budget.
- [ ] **Backstage2 production MCP key.**
  - Find the production Heroku app with `heroku pipelines:info <pipeline>`; the
    stage app is `backstage2-stage`.
  - Check that production serves the MCP endpoint: `curl -X POST
    https://<backstage2 host>/api/mcp` returns 403 without a key.
  - Add an entry named `stagehand-qvack`, **without** the `pii` scope, to the
    `MCP_API_KEYS` JSON list on the production app. Read the current value with
    `heroku config:get MCP_API_KEYS --app <app>` first, so existing keys are kept.

## 2. The image

- [ ] Merge `slack-agent-mvp` to `main`. The `stagehand-qvack` workflow then
  publishes `ghcr.io/rneventteknik/stagehand-qvack:main`. Until then, use the
  `:slack-agent-mvp` tag, which every push to the branch updates.
- [ ] Check the run passed under the repo's Actions tab.

## 3. Create the stack

In Portainer (portainer.rnevent.se, from the local network): **Stacks, Add
stack**.

- [ ] **Name:** `stagehand-qvack`.
- [ ] **Build method:** Repository.
  - **Repository URL:** `https://github.com/rneventteknik/agentic-framework`. The
    repo is public, so no authentication is needed.
  - **Repository reference:** `refs/heads/main`.
  - **Compose path:** `deploy/compose.yml`.
- [ ] **GitOps updates:** on, with **Polling** every `5m`.
  - **Re-pull image:** on, so each update pulls the latest
    `ghcr.io/rneventteknik/stagehand-qvack:main`.
  - **Force redeployment:** on. Without it, Portainer only redeploys when the
    repo's commit changes, and a new image on its own never would. With it,
    Portainer runs the update on every poll, and Compose only recreates the
    container when the pulled image differs from the running one
    ([Portainer FAQ](https://docs.portainer.io/faqs/troubleshooting/stacks-deployments-and-updates/how-do-automatic-updates-for-stacks-applications-work)).
- [ ] **Environment variables:** add the five values from step 1, with
  `BACKSTAGE2_MCP_URL=https://<backstage2 host>/api/mcp`. `deploy/compose.yml`
  lists these names under `environment:` without values, so Compose takes them
  from the stack's environment. Leave `LOG_LEVEL` out unless you need DEBUG;
  DEBUG logs every Slack event and model request, including booking data.
- [ ] **Deploy the stack.**

The first deploy pulls the image, which can take longer than the 60 seconds
Nginx Proxy Manager waits for `portainer.rnevent.se`. If the browser shows
`504 Gateway Time-out`, Portainer has stopped the deploy halfway; deploy again,
and the cached image makes it quick. Raising `proxy_read_timeout` and
`proxy_send_timeout` to `300s` under the proxy host's Advanced settings avoids
it.

Never use the production Slack tokens anywhere else, such as a laptop: a second
Socket Mode connection to the same app gets half of its messages.

## 4. Check it

- [ ] The container's logs in Portainer show `⚡️ Bolt app is running!`.
- [ ] In Slack, the production app answers "vilken utrustning är bokad på nästa
  gigg?" with a link to the booking. That question needs `search_bookings`
  followed by `get_booking`.
- [ ] After a restart of the container from Portainer, it answers again. The
  agent keeps no state that matters across restarts, apart from in-memory
  conversation history.

## 5. Updating

Merging to `main` is the deploy. The workflow publishes a new `:main` image, and
within one polling interval Portainer pulls it and recreates the container.
Changes to `deploy/compose.yml` arrive the same way.

- [ ] Merge a small change once, and check the container is recreated with the
  new image within about five minutes.
- [ ] To roll back, revert the change on `main`. To hold a specific version
  instead, set `image:` in `deploy/compose.yml` to a `sha-<commit>` tag; every
  published image has one.
- [ ] A redeploy restarts the container, which drops the in-memory conversation
  history. Threads continue, but without what was said before the restart.

## Good to know

- **Who can see the secrets.** Stack environment variables are stored in
  Portainer's database and shown to Portainer admins. They are also in backups of
  `docker-host`.
- **Logs** are capped at 3 × 10 MB by the logging options above. At `INFO`, they
  contain no message text or booking data.

## Later

Each of these replaces a manual step above. The details are in
[the plan](slack-agent.md#steps).

- **Pinned digests and Renovate.** Pin the image by digest instead of `:main`,
  and let Renovate propose the bumps. Each deploy is then a commit, and Force
  redeployment can be turned off.
- **LiteLLM** in front of Anthropic and backstage2, as part 2 of the plan.
