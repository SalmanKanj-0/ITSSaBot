import os
import logging
import time
import hashlib
import hmac
from flask import Request

logger = logging.getLogger(__name__)

SLACK_SIGNING_SECRET = os.environ["SLACK_SIGNING_SECRET"]

def verify_slack_request(request: Request):
    """
    Verifies the incoming Slack request using the signing secret.
    """
    try:
        timestamp = request.headers.get("X-Slack-Request-Timestamp")
        signature = request.headers.get("X-Slack-Signature")

        # Check if the request is recent to avoid replay attacks
        if abs(time.time() - int(timestamp)) > 60 * 5:
            logger.warning("Request timestamp is too old. Potential replay attack.")
            return False

        # Create the signature base string
        sig_basestring = f"v0:{timestamp}:{request.get_data(as_text=True)}"
        hashed = hmac.new(
            SLACK_SIGNING_SECRET.encode("utf-8"),
            sig_basestring.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Compare the computed signature with Slack's signature
        computed_signature = f"v0={hashed}"
        if not hmac.compare_digest(computed_signature, signature):
            logger.warning("Invalid Slack signature. Verification failed.")
            return False

        logger.info("Slack request verification successful.")
        return True
    except Exception as e:
        logger.error(f"Error verifying Slack request: {e}")
        return False
