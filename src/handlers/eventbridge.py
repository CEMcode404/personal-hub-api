from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from src.services.todo import process_notification

logger = Logger()

@logger.inject_lambda_context
def handler(event: dict, context: LambdaContext) -> dict:
    todo_id = event.get("todo_id")
    if not todo_id:
        logger.error("No todo_id in event")
        return {"status": "error", "message": "No todo_id provided"}
    process_notification(todo_id)
    return {"status": "ok"}