import logging
import json
from flask import Request
from slack_bolt.adapter.google_cloud_functions import SlackRequestHandler
from slack_controller import handle_message_events, handle_feedback_actions
from utils import verify_slack_request
from config import app, CONFLUENCE_BASE_URL, CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN
import requests
import openai

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
        return {
            "statusCode": 500,
            "body": "An error occurred while processing the request.",
        }

#def fetch_confluence_pages():
    """Fetch pages from Confluence using the API."""
    url = f"{CONFLUENCE_BASE_URL}/content"
    auth = (CONFLUENCE_USERNAME, CONFLUENCE_API_TOKEN)
    params = {"type": "page", "expand": "body.storage", "limit": 100}
    
    response = requests.get(url, auth=auth, params=params)
    response.raise_for_status()
    pages = response.json()["results"]
    
    # Extract content from pages
    content = [page["body"]["storage"]["value"] for page in pages]
    return content

#def train_openai_model_on_confluence(confluence_pages):
    """Train an OpenAI model using content from Confluence pages."""
    try:
        # Prepare data for fine-tuning
        training_data = [{"prompt": "", "completion": page[:200]} for page in confluence_pages]

        # OpenAI fine-tuning API call
        response = openai.FineTune.create(
            training_file=training_data,
            model="curie",
        )
        print(f"Fine-tuning job created: {response['id']}")
    except Exception as e:
        print(f"Error during fine-tuning: {e}")

#def ai_training_entry():
    """Entry point for AI training on Confluence pages."""
    try:
        # Fetch Confluence pages
        confluence_pages = fetch_confluence_pages()

        # Train OpenAI model
        train_openai_model_on_confluence(confluence_pages)
        return {"statusCode": 200, "body": "AI training initiated successfully."}
    except Exception as e:
        logger.error(f"Error during AI training: {e}")
        return {"statusCode": 500, "body": f"Error: {e}"}

def main(request: Request):
    """Entry point for Google Cloud Function"""
    path = request.path
    if path == "/slackbot":
        return slackbot(request)
    elif path == "/ai-training":
        return ai_training_entry()
    else:
        return {"statusCode": 404, "body": "Endpoint not found"}
