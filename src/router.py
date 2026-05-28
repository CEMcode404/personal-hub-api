from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from src.handlers.content import router as content
import os

print("APP_ENV:", os.environ.get("APP_ENV"))

app = APIGatewayHttpResolver(enable_validation=True);
app.include_router(content, prefix="/content")

if os.environ.get("APP_ENV") == "local":
    @app.get("/docs")
    def docs():
        return app.get_openapi_json_schema(title="Personal Hub API", version="1.0.0")