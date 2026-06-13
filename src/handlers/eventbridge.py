from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from src.repositories import todo as todo_repo
from src.services import notification as notification_service
from src.services.todo import handle_recurrence
from src.constants.todo import ScheduleAction

logger = Logger()

@logger.inject_lambda_context
def handler(event: dict, context: LambdaContext) -> dict:
    todo_id = event.get("todo_id")
    if not todo_id:
        logger.error("No todo_id in event")
        return {"status": "error", "message": "No todo_id provided"}

    todo = todo_repo.find_by_id(todo_id)
    if not todo:
        logger.warning(f"Todo {todo_id} not found")
        return {"status": "error", "message": "Todo not found"}

    action = event.get("action", ScheduleAction.notify.value)
    if action == ScheduleAction.recur.value:
        handle_recurrence(todo)
    else:
        notification_service.notify(todo)

    return {"status": "ok"}