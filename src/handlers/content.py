from aws_lambda_powertools.event_handler.api_gateway import Router
from src.services import content as content_service
from src.constants.content import ContentStatus
from src.utils.response import success, handle_errors
from src.utils.query_params import parse_int, parse_cursor, parse_str

router = Router()


@router.get("")
@handle_errors
def list_public_content():
    params = router.current_event.query_string_parameters or {}
    limit = parse_int(params.get("limit"), default=10, min_val=1, max_val=100)
    cursor = parse_cursor(params.get("cursor"))
    type = parse_str(params.get("type"))
    result = content_service.list_all(
        limit=limit, cursor=cursor, status=ContentStatus.published.value, type=type
    )
    return success(result)


@router.get("/slug/<slug>")
@handle_errors
def get_public_content_by_slug(slug: str):
    item = content_service.get_by_slug(slug)
    if item.get("status") != ContentStatus.published.value:
        raise ValueError("Content not found")
    return success(item)