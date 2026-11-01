from logging import Logger

from slack_bolt import BoltContext, Say, SayStream, SetStatus
from slack_sdk import WebClient

from agent import AgentDeps, run_agent
from thread_context import conversation_store


def handle_message(
    client: WebClient,
    context: BoltContext,
    event: dict,
    logger: Logger,
    say: Say,
    say_stream: SayStream,
    set_status: SetStatus,
):
    """Handle messages sent to the agent via DM or in threads the bot is part of."""
    # Skip message subtypes (edits, deletes, etc.) and bot messages.
    if event.get("subtype"):
        return
    if event.get("bot_id"):
        return

    is_dm = event.get("channel_type") == "im"
    is_thread_reply = event.get("thread_ts") is not None

    if is_dm:
        pass
    elif is_thread_reply:
        # Channel thread replies are handled only if the bot is already engaged
        history = conversation_store.get_history(context.channel_id, event["thread_ts"])
        if history is None:
            return
    else:
        # Top-level channel messages are handled by app_mentioned
        return

    try:
        channel_id = context.channel_id
        text = event.get("text", "")
        thread_ts = event.get("thread_ts") or event["ts"]

        user_id = context.user_id

        # Get conversation history
        history = conversation_store.get_history(channel_id, thread_ts)

        # Set assistant thread status with loading messages
        set_status(
            status="Tänker...",
            loading_messages=[
                "Rullar kablar med Över-Under tekniken…",
                "Kånkar scen-podie, sköldpadde-style…",
                "Hashmeckar lite bara…",
                "Väntar på hissen…",
                "Packar caset…",
                "Byter glödlampa…",
                "Finjusterar EQ:n…",
                "Kollar vem det var som ringde på klockan...",
                "Prisförhandlar med Q...",
                "Fastnat i hissen...",
                "Letar efter 42:an...",
                "På väg tillbka från R1...",
                "Tar lite extra ström från uttaget bakom scenen...",
                "Tömmer diskmaskinen...",
                "Hämtar paket i KårX...",
                "Hämtar chirre med dirre...",
                "Riktar fronten...",
                "Glömde dra upp mastern...",
                "Larmar på...",
                "Lämnar ut en hyra...",
                "Äter nattamat...",
                "Letar i kylen efter bågot gott...",
                "Mäter dB nivån i Nya...",
                "Hisar 315... ",
                "Förhandlar muta med proggo...",
                "Toapaus...",
                "Dansa... Pausa...",
                "Fnissar åt inlägg i #skit...",
                "Damsugar på kontoret...",
            ],
        )

        # Run the agent
        deps = AgentDeps(
            client=client,
            user_id=user_id,
            channel_id=channel_id,
            thread_ts=thread_ts,
            message_ts=event["ts"],
            user_token=context.user_token,
        )
        result = run_agent(text, deps, message_history=history)

        streamer = say_stream()
        streamer.append(markdown_text=result.output)
        streamer.stop()

        # Store conversation history
        conversation_store.set_history(channel_id, thread_ts, result.all_messages())

    except Exception as e:
        logger.exception("Failed to handle message")
        say(
            text=f":warning: Något gick fel! ({e})",
            thread_ts=event.get("thread_ts") or event.get("ts"),
        )
