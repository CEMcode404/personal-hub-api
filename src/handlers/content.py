from typing import Annotated
from aws_lambda_powertools.event_handler.api_gateway import Router
from src.services import content as content_service
from aws_lambda_powertools.event_handler.openapi.params import Body
from src.schemas.content import CreateContentRequest, UpdateContentRequest
from src.utils.response import success, handle_errors
import json

router = Router()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("")
@handle_errors
def list_content():
    params = router.current_event.query_string_parameters or {}
    limit = int(params.get("limit", 10))
    cursor_str = params.get("cursor")
    cursor = json.loads(cursor_str) if cursor_str else None
    result = content_service.list_all(limit=limit, cursor=cursor)
    return success(result)

@router.post("")
@handle_errors
def create_content(body: Annotated[CreateContentRequest, Body()]):
    result = content_service.create(body)
    return success(result.__dict__, status_code=201)

@router.patch("/<id>")
@handle_errors
def update_content(id: str, body: Annotated[UpdateContentRequest, Body()]):
    return success(content_service.update(id, body))

@router.delete("/<id>")
@handle_errors
def delete_content(id: str):
    content_service.delete(id)
    return success({"message": "Content deleted"})