from aws_lambda_powertools.event_handler.api_gateway import Router
from src.repositories import notification as notification_repo
from src.utils.response import success, handle_errors

router = Router()

@router.get("")
@handle_errors
def list_notifications():
    result = notification_repo.find_all()
    return success({"items": result})

@router.get("/unread")
@handle_errors
def list_unread():
    result = notification_repo.find_unread()
    return success({"items": result})

@router.patch("/<id>/read")
@handle_errors
def mark_as_read(id: str):
    notification_repo.mark_as_read(id)
    return success({"message": "Notification marked as read"})