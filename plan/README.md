# Plan

Implementation plans: what is going to be built, in what order, and how we will
know each step works. Unlike [research/](../research/README.md), which weighs
options, a plan here is a commitment to try something. When a step turns out
differently than planned, the plan is updated to match.

## Contents

### [Slack agent, then a LiteLLM gateway](slack-agent.md)
The first running slice. A Pydantic AI agent in Slack, set up with the Slack CLI,
answers questions using the Anthropic API and the backstage2 MCP server, and runs
on our Proxmox host. No inbound ports are opened; deploys are pulled by the host
instead of pushed by CI. Once that runs, a self-hosted LiteLLM gateway moves the
keys, budgets and MCP access in front of it.

### [Deploy TODO](deploy-todo.md)
The fastest way to get the agent running: a Portainer stack on the existing
`docker-host` VM, pulling the image GitHub Actions publishes to GHCR. Checklist
form, with the automation from the plan listed as later replacements for each
manual step.
