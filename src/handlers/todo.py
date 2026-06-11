from typing import Annotated
from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.event_handler.openapi.params import Body
from src.services import todo as todo_service
from src.schemas.todo import CreateTodoRequest, UpdateTodoRequest
from src.utils.response import success, handle_errors
from src.utils.query_params import parse_int, parse_cursor

router = Router()

@router.get("")
@handle_errors
def list_todos():
    params = router.current_event.query_string_parameters or {}
    limit = parse_int(params.get("limit"), default=10, min_val=1, max_val=100)
    cursor = parse_cursor(params.get("cursor"))
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
    return success(todo_service.update(id, body))

@router.delete("/<id>")
@handle_errors
def delete_todo(id: str):
    todo_service.delete(id)
    return success({"message": "Todo deleted"})