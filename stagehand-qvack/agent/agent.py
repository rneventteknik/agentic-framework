import logging
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic_ai import Agent, UsageLimits
from pydantic_ai.mcp import MCPToolset

from agent.deps import AgentDeps

SYSTEM_PROMPT = Path(__file__).with_name("system_prompt.md").read_text(encoding="utf-8")
STOCKHOLM = ZoneInfo("Europe/Stockholm")
WEEKDAYS_SV = (
    "måndag",
    "tisdag",
    "onsdag",
    "torsdag",
    "fredag",
    "lördag",
    "söndag",
)

logger = logging.getLogger(__name__)

_cached_model: str | None = None


def get_model() -> str:
    """Select the AI model based on available API keys.

    Prefers Anthropic when both keys are set.
    """
    global _cached_model
    if _cached_model is not None:
        return _cached_model

    if os.environ.get("ANTHROPIC_API_KEY"):
        _cached_model = "anthropic:claude-haiku-5-5"
    elif os.environ.get("OPENAI_API_KEY"):
        _cached_model = "openai:gpt-4.1-mini"
    else:
        raise RuntimeError(
            "No AI provider configured. "
            "Set ANTHROPIC_API_KEY or OPENAI_API_KEY in your environment."
        )
    return _cached_model


SLACK_MCP_URL = "https://mcp.slack.com/mcp"

MAX_MODEL_REQUESTS_PER_MESSAGE = 10


def get_backstage2_toolset() -> MCPToolset:
    url = os.environ.get("BACKSTAGE2_MCP_URL")
    key = os.environ.get("BACKSTAGE2_MCP_KEY")
    if not url or not key:
        raise RuntimeError(
            "Backstage2 MCP not configured. "
            "Set BACKSTAGE2_MCP_URL and BACKSTAGE2_MCP_KEY in your environment."
        )
    return MCPToolset(
        url,
        headers={"Authorization": f"Bearer {key}"},
        tool_error_behavior="failed",
    )


agent = Agent(
    deps_type=AgentDeps,
    system_prompt=SYSTEM_PROMPT,
)


@agent.instructions
def current_date_instructions() -> str:
    now = datetime.now(STOCKHOLM)
    weekday = WEEKDAYS_SV[now.weekday()]
    return f"Dagens datum är {now:%Y-%m-%d} ({weekday}, Europe/Stockholm)."


def run_agent(text, deps, message_history=None):
    """Run the agent with the Backstage2 MCP server, and the Slack MCP server when a user token is present."""
    toolsets = [get_backstage2_toolset()]
    if deps.user_token:
        logger.info("Slack MCP Server enabled (user_token present)")
        toolsets.append(
            MCPToolset(
                SLACK_MCP_URL,
                headers={"Authorization": f"Bearer {deps.user_token}"},
            )
        )
    else:
        logger.info("Slack MCP Server disabled (no user_token)")

    return agent.run_sync(
        text,
        model=get_model(),
        deps=deps,
        message_history=message_history,
        toolsets=toolsets,
        usage_limits=UsageLimits(request_limit=MAX_MODEL_REQUESTS_PER_MESSAGE),
    )
