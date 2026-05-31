from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, CORSConfig
from src.handlers.content import router as content
from src.handlers.research import router as research
from src.handlers.todo import router as todo
from src.handlers.notification import router as notification
import os

cors_config = CORSConfig(
    allow_origin="http://localhost:5173" if os.environ.get("APP_ENV") == "local" else "https://your-cloudfront-domain.com",
    allow_headers=["Authorization", "Content-Type"],
    max_age=300,
)

app = APIGatewayHttpResolver(enable_validation=True, cors=cors_config);
app.include_router(content, prefix="/content")
app.include_router(research, prefix="/research")
app.include_router(todo, prefix="/todo")
app.include_router(notification, prefix="/notifications")

if os.environ.get("APP_ENV") == "local":
    @app.get("/docs")
    def docs():
        return app.get_openapi_json_schema(title="Personal Hub API", version="1.0.0")