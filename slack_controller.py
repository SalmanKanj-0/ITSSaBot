import logging
import time
import json
from slack_bolt import App
from slack_bolt.adapter.google_cloud_functions import SlackRequestHandler
from ai_controller import get_openai_response, summarize_message
from jira_controller import create_jira_ticket
from sheet_controller import append_to_sheet_async
from config import TICKET_CREATION_URL, bot_user_id

logger = logging.getLogger(__name__)

def handle_message_events(app: App):
    @app.event("message")
    def message_event_handler(body, say, client):
        """
        Handles messages and shows a sand clock animation while processing. Ensures replies are in a thread.
        """
        try:
            event = body["event"]
            user_id = event.get("user")
            user_message = event.get("text", "").strip()
            channel_type = event.get("channel_type")  # 'channel', 'group', 'im'

            # Ignore messages we don't need to process
            if should_ignore_message(event, user_id, channel_type):
                return

            if not user_message:
                logger.warning("No text found in the message event. Skipping.")
                return

            # Get the channel ID and thread timestamp
            channel_id = event.get("channel")
            thread_ts = event.get("thread_ts", event.get("ts"))

            # Send sand clock animation
            initial_message_ts = send_sand_clock_animation(client, channel_id, thread_ts)

            # Process the user message
            bot_response = get_openai_response(user_message)

            # Construct and send the bot's reply
            send_bot_reply(client, channel_id, initial_message_ts, bot_response)

        except Exception as e:
            logger.error("Error handling message event: %s", str(e))
            say(text="Sorry, something went wrong. Please try again later.")

def should_ignore_message(event, user_id, channel_type):
    """
    Determines whether to ignore the incoming message.
    """
    # 1) Ignore direct messages, bot messages, message deletions, channel joins, or messages from the bot itself
    if (
        channel_type == "im"
        or event.get("subtype") in ["bot_message", "message_deleted", "channel_join"]
        or user_id == bot_user_id
    ):
        return True
    
    # 2) Ignore subsequent messages in a thread (replies)
    #    If a message has a 'thread_ts' and it's different from 'ts',
    #    it means it's a reply in a thread instead of the root message
    if "thread_ts" in event and event["thread_ts"] != event["ts"]:
        return True
    
    return False


def send_sand_clock_animation(client, channel_id, thread_ts):
    """
    Sends a sand clock animation in the thread and returns the message timestamp.
    """
    initial_message = client.chat_postMessage(
        channel=channel_id, text="⏳ Thinking...", thread_ts=thread_ts
    )
    initial_message_ts = initial_message["ts"]

    sand_clock_steps = ["⏳ Thinking...", "⌛ Still working...", "⏳ Almost done..."]
    for step in sand_clock_steps:
        client.chat_update(
            channel=channel_id,
            ts=initial_message_ts,
            text=step,
        )
        time.sleep(1)
    return initial_message_ts

def send_bot_reply(client, channel_id, message_ts, bot_response):
    """
    Constructs and sends the bot's reply, replacing the sand clock message.
    """
    bot_reply = f"{bot_response}\n\n*Please let me know if this answer is sufficient!*"

    feedback_blocks = [
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": bot_reply},
        },
        {
            "type": "actions",
            "block_id": "feedback_buttons",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "👍 Yes"},
                    "action_id": "feedback_positive",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "👎 No"},
                    "action_id": "feedback_negative",
                },
            ],
        },
    ]

    client.chat_update(
        channel=channel_id,
        ts=message_ts,
        text=bot_reply,
        blocks=feedback_blocks,
    )

def handle_feedback_actions(app: App):
    @app.action("feedback_positive")
    def handle_positive_feedback(ack, body, client):
        ack()
        try:
            process_feedback(body, client, positive_feedback=True)
        except Exception as e:
            logger.error("Error handling positive feedback: %s", str(e))

    @app.action("feedback_negative")
    def handle_negative_feedback(ack, body, client):
        ack()
        try:
            process_feedback(body, client, positive_feedback=False)
        except Exception as e:
            logger.error("Error handling negative feedback: %s", str(e))

def process_feedback(body, client, positive_feedback):
    """
    Processes user feedback, updates the message, and takes appropriate actions.
    """
    thread_ts = body["container"]["thread_ts"]
    message_ts = body["container"]["message_ts"]
    channel_id = body["container"]["channel_id"]
    user_id = body["user"]["id"]

    # Get user's email
    user_email, user_name = get_user_email_and_name(client, user_id)
    if not user_email:
        logger.error("Unable to retrieve user's email.")
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text="Unable to retrieve your email. Please contact support manually.",
        )
        return

    # Update the original message
    update_original_message(client, body, channel_id, message_ts, positive_feedback)

    # Handle feedback
    if positive_feedback:
        handle_positive_feedback_action(client, channel_id, thread_ts, user_email)
    else:
        handle_negative_feedback_action(client, channel_id, thread_ts, user_id, user_email)

def get_user_email_and_name(client, user_id):
    """
    Retrieves the user's email and name from Slack.
    """
    user_info = client.users_info(user=user_id)
    user_profile = user_info.get('user', {}).get('profile', {})
    user_email = user_profile.get('email')
    user_name = user_profile.get('real_name') or user_profile.get('display_name') or user_id
    return user_email, user_name

def update_original_message(client, body, channel_id, message_ts, positive_feedback):
    """
    Updates the original message to remove feedback buttons and add feedback received context.
    """
    feedback_text = "👍" if positive_feedback else "👎"
    original_blocks = body["message"]["blocks"]
    modified_blocks = [
        block for block in original_blocks if block.get("block_id") != "feedback_buttons"
    ]
    modified_blocks.append(
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": f"Feedback received: {feedback_text}"}],
        }
    )
    client.chat_update(
        channel=channel_id,
        ts=message_ts,
        text=body["message"]["text"],
        blocks=modified_blocks,
    )

def handle_positive_feedback_action(client, channel_id, thread_ts, user_email):
    """
    Handles actions after receiving positive feedback.
    """
    # Append feedback asynchronously
    ticket_number = "AI_Ticket"
    feedback = "Positive Feedback"
    append_to_sheet_async(ticket_number, feedback, user_email)

    # Reply in thread
    client.chat_postMessage(
        channel=channel_id,
        thread_ts=thread_ts,
        text="Thank you for your feedback! 😊 I'm glad I could help!",
    )

def handle_negative_feedback_action(client, channel_id, thread_ts, user_id, user_email):
    """
    Handles actions after receiving negative feedback, including creating a Jira ticket.
    """
    # Get the user's original message from the thread
    user_message = get_user_original_message(client, channel_id, thread_ts, user_id)

    # Summarize the user message for the Jira ticket summary
    ticket_summary = summarize_message(user_message)

    # Create a Jira ticket
    issue_key, ticket_url = create_jira_ticket(
        summary=ticket_summary,
        description=user_message,
        reporter_email=user_email,
        project_key="SD",
        request_type_name="Get IT help"
    )

    if issue_key and ticket_url:
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text=f"I'm sorry I couldn't resolve your query. A support ticket has been created for you: <{ticket_url}|{issue_key}>. Our team will get back to you shortly.",
        )
    else:
        client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text="I'm sorry I couldn't resolve your query, and there was an error creating a support ticket automatically. Please use the button below to create a ticket manually.",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Please use the button below to create a ticket:",
                    },
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Create Ticket"},
                            "url": TICKET_CREATION_URL,
                            "action_id": "create_ticket_button",
                        },
                    ],
                },
            ],
        )

def get_user_original_message(client, channel_id, thread_ts, user_id):
    """
    Retrieves the user's original message from the thread.
    """
    response = client.conversations_replies(channel=channel_id, ts=thread_ts)
    messages = response["messages"]
    for msg in messages:
        if msg.get("user") == user_id:
            return msg.get("text")
    return "User message not found."
