import json
from typing import Annotated
from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.event_handler.openapi.params import Body
from src.services import todo as todo_service
from src.schemas.todo import CreateTodoRequest, UpdateTodoRequest
from src.utils.response import success, handle_errors

router = Router()

@router.get("")
@handle_errors
def list_todos():
    params = router.current_event.query_string_parameters or {}
    limit = int(params.get("limit", 10))
    cursor_str = params.get("cursor")
    cursor = json.loads(cursor_str) if cursor_str else None
    result = todo_service.list_all(limit=limit, cursor=cursor)
    return success(result)

@router.get("/<id>")
@handle_errors
def get_todo(id: str):
    return success(todo_service.get_by_id(id))

@router.post("")
@handle_errors
def create_todo(body: Annotated[CreateTodoRequest, Body()]):
    result = todo_service.create(body)
    return success(result.__dict__, status_code=201)

@router.patch("/<id>")
@handle_errors
def update_todo(id: str, body: Annotated[UpdateTodoRequest, Body()]):
    result = todo_service.update(id, body)
    return success(result)

@router.delete("/<id>")
@handle_errors
def delete_todo(id: str):
    todo_service.delete(id)
    return success({"message": "Todo deleted"})