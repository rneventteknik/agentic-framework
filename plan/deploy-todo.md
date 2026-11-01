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
- [ ] **Build method:** Web editor, with this compose file:

  ```yaml
  services:
    stagehand-qvack:
      image: ghcr.io/rneventteknik/stagehand-qvack:main
      restart: unless-stopped
      environment:
        ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
        BACKSTAGE2_MCP_URL: ${BACKSTAGE2_MCP_URL}
        BACKSTAGE2_MCP_KEY: ${BACKSTAGE2_MCP_KEY}
        SLACK_BOT_TOKEN: ${SLACK_BOT_TOKEN}
        SLACK_APP_TOKEN: ${SLACK_APP_TOKEN}
        LOG_LEVEL: ${LOG_LEVEL:-INFO}
      logging:
        driver: json-file
        options:
          max-size: 10m
          max-file: "3"
  ```

- [ ] **Environment variables:** add the five values from step 1, with
  `BACKSTAGE2_MCP_URL=https://<backstage2 host>/api/mcp`. Portainer substitutes
  them into the `${...}` references above. Leave `LOG_LEVEL` out unless you need
  DEBUG; DEBUG logs every Slack event and model request, including booking data.
- [ ] **Deploy the stack.**

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

After a change is merged to `main` and its workflow run has passed: in Portainer,
open the stack, choose **Update the stack**, and turn on **Re-pull image and
redeploy**.

- [ ] Do it once after a small change, to know it works.
- [ ] To roll back, change the image tag in the editor to a previous
  `sha-<commit>` tag and update the stack. Every published image has one.

## Good to know

- **Who can see the secrets.** Stack environment variables are stored in
  Portainer's database and shown to Portainer admins. They are also in backups of
  `docker-host`.
- **Logs** are capped at 3 × 10 MB by the logging options above. At `INFO`, they
  contain no message text or booking data.

## Later

Each of these replaces a manual step above. The details are in
[the plan](slack-agent.md#steps).

- **A Git repository stack with GitOps updates.** Point the stack at this repo
  instead of the web editor, and let Portainer poll `main`, so merging redeploys
  without step 5. `deploy/compose.yml` would need its environment written as
  `${...}` references like the compose file above.
- **Pinned digests and Renovate.** Pin the image by digest instead of `:main`, and
  let Renovate propose the bumps.
- **LiteLLM** in front of Anthropic and backstage2, as part 2 of the plan.
