import logging
import json
from flask import Request
from slack_bolt.adapter.google_cloud_functions import SlackRequestHandler
from slack_controller import handle_message_events, handle_feedback_actions
from utils import verify_slack_request
from config import app

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Register event handlers
handle_message_events(app)
handle_feedback_actions(app)

# Google Cloud Function entry point
slack_handler = SlackRequestHandler(app)

def slackbot(request):
    try:
        # Verify Slack request
        if not verify_slack_request(request):
            return {"statusCode": 403, "body": "Invalid request"}

        # Check for retry headers
        retry_num = request.headers.get("X-Slack-Retry-Num")
        if retry_num and int(retry_num) > 0:
            logger.info(f"Ignoring Slack retry: X-Slack-Retry-Num={retry_num}")
            return {"statusCode": 200, "body": "Ignoring retry"}

        request_json = request.get_json(silent=True)

        # Handle Slack URL verification challenge
        if (
            request_json
            and "type" in request_json
            and request_json["type"] == "url_verification"
        ):
            challenge = request_json["challenge"]
            return {"statusCode": 200, "body": challenge}

        # Process Slack interactions
        if "payload" in request.form:
            payload = json.loads(request.form["payload"])
            logger.info(f"Interaction payload received: {payload}")

        # Process Slack events
        return slack_handler.handle(request)
    except Exception as e:
        logger.error(f"Error handling request: {e}")
        return {"statusCode": 500, "body": "Internal server error"}

