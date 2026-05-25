import json
import os
import uuid
from datetime import datetime, timezone

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, Response
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
app = APIGatewayHttpResolver()

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

@app.get("/health")
def health():
    return {"status": "ok"}

# fix the content endpoint error
# @app.get("/content")
# def list_content():
#     result = table.scan()
#     return {"items": result["Items"]}

# @app.post("/content")
# def create_content():
#     body = app.current_event.json_body
    
#     if not body.get("title"):
#         return Response(status_code=400, body=json.dumps({"error": "title is required"}))
    
#     item = {
#         "id": str(uuid.uuid4()),
#         "title": body.get("title"),
#         "body": body.get("body"),
#         "type": body.get("type", "article"),
#         "status": "draft",
#         "createdAt": datetime.now(timezone.utc).isoformat(),
#     }
#     table.put_item(Item=item)
#     return Response(status_code=201, body=json.dumps(item))


@logger.inject_lambda_context
def handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)