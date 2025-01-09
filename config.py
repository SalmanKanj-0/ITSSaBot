import os
import logging

logger = logging.getLogger(__name__)

# Environment Variables
try:
    SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
    SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
    TICKET_CREATION_URL = os.environ.get(
        "TICKET_CREATION_URL",
        "https://catawiki.atlassian.net/servicedesk/customer/portal/21/group/-1",
    )
except KeyError as e:
    logger.error(f"Environment variable {str(e)} not set. Exiting.")
    raise

# Initialize OpenAI API key
import openai
openai.api_key = OPENAI_API_KEY

# Slack App Initialization
from slack_bolt import App
app = App(token=SLACK_BOT_TOKEN)

# Retrieve Bot User ID
try:
    bot_user_id = app.client.auth_test()["user_id"]
    logger.info(f"Bot User ID: {bot_user_id}")
except Exception as e:
    logger.error(f"Error getting bot user ID: {e}")
    bot_user_id = None

# Confluence API Configuration
#CONFLUENCE_BASE_URL = "https://your-confluence-instance.atlassian.net/wiki/rest/api/"
#CONFLUENCE_USERNAME = "your-username"
#CONFLUENCE_API_TOKEN = "your-api-token"

