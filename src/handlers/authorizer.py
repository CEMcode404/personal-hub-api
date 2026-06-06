import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """
    Lambda authorizer that validates the x-origin-secret header.
    Secret is injected via environment variable from SSM at deploy time.
    Uses simple response format (EnableSimpleResponses: true).
    Returns True = authorized, False = 403 Forbidden.
    """
    app_env = os.environ.get("APP_ENV", "")
    if app_env == "local":
        return {"isAuthorized": True}
    
    try:
        headers = event.get("headers", {})
        request_secret = headers.get("x-origin-secret")

        if not request_secret:
            logger.warning("Request rejected: missing x-origin-secret header")
            return {"isAuthorized": False}

        expected_secret = os.environ.get("ORIGIN_SECRET")
        if request_secret != expected_secret:
            logger.warning("Request rejected: invalid x-origin-secret value")
            return {"isAuthorized": False}

        return {"isAuthorized": True}

    except Exception as e:
        logger.error(f"Authorizer error: {e}")
        return {"isAuthorized": False}