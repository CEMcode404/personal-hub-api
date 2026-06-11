from typing import Annotated
from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.event_handler.openapi.params import Body
from src.services import research as research_service
from src.schemas.research import CreateResearchRequest, UpdateResearchRequest
from src.utils.response import success, handle_errors
from src.utils.query_params import parse_int, parse_cursor

router = Router()

@router.get("")
@handle_errors
def list_research():
    params = router.current_event.query_string_parameters or {}
    limit = parse_int(params.get("limit"), default=10, min_val=1, max_val=100)
    cursor = parse_cursor(params.get("cursor"))
    result = research_service.list_all(limit=limit, cursor=cursor)
    return success(result)

@router.get("/<id>")
@handle_errors
def get_research(id: str):
    return success(research_service.get_by_id(id))

@router.post("")
@handle_errors
def create_research(body: Annotated[CreateResearchRequest, Body()]):
    result = research_service.create(body)
    return success(result.__dict__, status_code=201)

@router.patch("/<id>")
@handle_errors
def update_research(id: str, body: Annotated[UpdateResearchRequest, Body()]):
    return success(research_service.update(id, body))

@router.delete("/<id>")
@handle_errors
def delete_research(id: str):
    research_service.delete(id)
    return success({"message": "Research deleted"})