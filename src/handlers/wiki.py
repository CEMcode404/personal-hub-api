from typing import Annotated
from aws_lambda_powertools.event_handler.api_gateway import Router
from aws_lambda_powertools.event_handler.openapi.params import Body
from src.services import wiki as wiki_service
from src.schemas.wiki import CreateWikiRequest, UpdateWikiRequest
from src.utils.response import success, handle_errors
from src.utils.query_params import parse_int, parse_cursor, parse_str

router = Router()

@router.get("")
@handle_errors
def list_wiki():
    params = router.current_event.query_string_parameters or {}
    limit = parse_int(params.get("limit"), default=10, min_val=1, max_val=100)
    cursor = parse_cursor(params.get("cursor"))
    tag = parse_str(params.get("tag"))
    category = parse_str(params.get("category"))
    result = wiki_service.list_all(limit=limit, cursor=cursor, tag=tag, category=category)
    return success(result)

@router.get("/<id>")
@handle_errors
def get_wiki(id: str):
    return success(wiki_service.get_by_id(id))

@router.post("")
@handle_errors
def create_wiki(body: Annotated[CreateWikiRequest, Body()]):
    result = wiki_service.create(body)
    return success(result.__dict__, status_code=201)

@router.patch("/<id>")
@handle_errors
def update_wiki(id: str, body: Annotated[UpdateWikiRequest, Body()]):
    return success(wiki_service.update(id, body))

@router.delete("/<id>")
@handle_errors
def delete_wiki(id: str):
    wiki_service.delete(id)
    return success({"message": "Wiki deleted"})