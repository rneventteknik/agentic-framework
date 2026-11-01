import os

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from agent import get_backstage2_toolset, get_model
from listeners import register_listeners
from log_config import configure_logging

load_dotenv(dotenv_path=".env", override=False)
configure_logging()
get_model()  # Fail fast if no AI provider key is configured
get_backstage2_toolset()

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

register_listeners(app)

if __name__ == "__main__":
    SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN")).start()
