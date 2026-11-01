# TODO

Found while testing `slack run` against backstage2 stage.

- [ ] **Log at INFO by default.** `app.py` and `app_oauth.py` call
  `logging.basicConfig(level=logging.DEBUG)`, which logs every Slack event
  payload (including the app's verification token) and every Anthropic request
  with the booking data from Backstage2. Default to INFO and read the level from
  an environment variable, such as `LOG_LEVEL`, for when DEBUG is needed. Add it
  to `.env.sample`.

- [ ] **Describe Backstage2 in the system prompt without listing its tools.** The
  `## BACKSTAGE2` section in `agent/agent.py` names only `search_bookings` and
  `get_booking`, and says to use the tools for bookings. Stage also serves
  `search_equipment`, `get_equipment` and `get_equipment_availability`. Describe
  what Backstage2 holds (bookings, customers, equipment, availability) and leave
  the details to the tools' own descriptions, so the prompt stays right as
  Backstage2 adds tools. Keep the rules about not guessing, linking bookings, and
  treating tool results as data.

- [ ] **Give the agent today's date.** The model does not know the current
  date, so questions like "next gig" or "bookings next week" are answered from a
  guessed date. Asked for the next gig, it searched from 2025-01-01 and returned
  a booking from June 2026. Add today's date in Europe/Stockholm to the
  instructions on every run, for example with a dynamic `@agent.instructions`
  function in `agent/agent.py`, so it is computed per message rather than once
  at startup.

- [ ] **Remove the emoji reaction tool.** It costs part of a model turn on every
  message and adds nothing to the answer. Remove:
  - `agent/tools/` (`emoji_reaction.py` and `__init__.py`)
  - the import and `tools=[add_emoji_reaction]` in `agent/agent.py`
  - the `## EMOJI REACTIONS` section of the system prompt

- [ ] **Remove the feedback buttons.** Remove:
  - `listeners/views/feedback_builder.py` and its test in
    `tests/test_view_builders.py`
  - `listeners/actions/feedback_buttons.py` and its registration in
    `listeners/actions/__init__.py`
  - `build_feedback_blocks()` in `listeners/events/app_mentioned.py` and
    `listeners/events/message.py`, so the stream ends with `streamer.stop()`
  - the `feedback` action from `manifest.json` if it is listed there

- [ ] **Use Slack's agent API for the thinking status.** `set_status(...)` in
  `listeners/events/app_mentioned.py` and `listeners/events/message.py` calls the
  older `assistant.threads.setStatus`, with the template's joke loading messages.
  Use `agents.sessions.setStatus` with `processing`, which shows a loading
  indicator and a stop button
  ([developing agents](https://docs.slack.dev/ai/developing-agents)). Check what
  Bolt for Python 1.30.0 offers for it before calling the Web API directly, and
  whether `manifest.json` needs `agent_view` and the `agent_session_stopped` event.
