import json
from typing import Annotated
from aws_lambda_powertools.event_handler import Response
from aws_lambda_powertools.event_handler.api_gateway import Router
from src.services import content as content_service
from aws_lambda_powertools.event_handler.openapi.params import Body
from src.schemas.content import CreateContentRequest

router = Router()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("")
def list_content():
    return {"items": content_service.list_all()}

@router.post("")
def create_content(body: Annotated[CreateContentRequest, Body()]):
    try:
        result = content_service.create(body)
        return Response(status_code=201, content_type="application/json", body=json.dumps(result.__dict__))
    except ValueError as e:
        return Response(status_code=400, content_type="application/json", body=json.dumps({"error": str(e)}))
    except Exception as e:
        return Response(status_code=500, content_type="application/json", body=json.dumps({"error": "Internal server error"}))