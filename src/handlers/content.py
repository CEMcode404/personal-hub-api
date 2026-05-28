from typing import Annotated
from aws_lambda_powertools.event_handler.api_gateway import Router
from src.services import content as content_service
from aws_lambda_powertools.event_handler.openapi.params import Body
from src.schemas.content import CreateContentRequest, UpdateContentRequest
from src.utils.response import success, handle_errors

router = Router()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("")
def list_content():
    return {"items": content_service.list_all()}

@router.post("")
@handle_errors
def create_content(body: Annotated[CreateContentRequest, Body()]):
    result = content_service.create(body)
    return success(result.__dict__, status_code=201)

@router.patch("/<id>")
@handle_errors
def update_content(id: str, body: Annotated[UpdateContentRequest, Body()]):
    return success(content_service.update(id, body))