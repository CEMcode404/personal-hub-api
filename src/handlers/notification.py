from aws_lambda_powertools.event_handler.api_gateway import Router
from src.repositories import notification as notification_repo
from src.utils.response import success, handle_errors
from src.utils.query_params import parse_int, parse_cursor

router = Router()

@router.get("")
@handle_errors
def list_notifications():
    params = router.current_event.query_string_parameters or {}
    limit = parse_int(params.get("limit"), default=10, min_val=1, max_val=100)
    cursor = parse_cursor(params.get("cursor"))
    result = notification_repo.find_all(limit=limit, cursor=cursor)
    return success(result)

@router.get("/unread")
@handle_errors
def list_unread():
    params = router.current_event.query_string_parameters or {}
    limit = parse_int(params.get("limit"), default=10, min_val=1, max_val=100)
    cursor = parse_cursor(params.get("cursor"))
    result = notification_repo.find_unread(limit=limit, cursor=cursor)
    return success(result)

@router.patch("/<id>/read")
@handle_errors
def mark_as_read(id: str):
    notification_repo.mark_as_read(id)
    return success({"message": "Notification marked as read"})