from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from src.handlers.content import router as content

app = APIGatewayHttpResolver();
app.include_router(content, prefix="/content")
