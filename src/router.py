from aws_lambda_powertools.event_handler import APIGatewayHttpResolver, CORSConfig
from src.handlers.content import router as content
from src.handlers.research import router as research
from src.handlers.todo import router as todo
from src.handlers.notification import router as notification
from src.handlers.wiki import router as wiki
import os

cors_config = CORSConfig(
    allow_origin=os.environ.get("ALLOWED_ORIGIN", "http://localhost:5173"),
    allow_headers=["Authorization", "Content-Type"],
    max_age=300,
)

app = APIGatewayHttpResolver(enable_validation=True, cors=cors_config);

admin_routers = {
    "/content":      content,
    "/research":     research,
    "/todo":         todo,
    "/notifications": notification,
    "/wiki":         wiki,
}

for path, router in admin_routers.items():
    app.include_router(router, prefix=f"{path}")

if os.environ.get("APP_ENV") == "local":
    @app.get("/docs")
    def docs():
        return app.get_openapi_json_schema(title="Personal Hub API", version="1.0.0")