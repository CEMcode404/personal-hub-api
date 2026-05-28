import json
from aws_lambda_powertools.event_handler import Response
from aws_lambda_powertools.event_handler.api_gateway import Router
from src.services import content as content_service

router = Router()

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("")
def list_content():
    return {"items": content_service.list_all()}

@router.post("")
def create_content():
    try:
        body = router.current_event.json_body
        return content_service.create(body)
    except ValueError as e:
        return Response(status_code=400, content_type="application/json", body=json.dumps({"error": str(e)}))