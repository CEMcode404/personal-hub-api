import os

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from src.router import app

print("ENDPOINT:", os.environ.get("DYNAMODB_ENDPOINT_URL"))
print("KEY:", os.environ.get("AWS_ACCESS_KEY_ID"))

logger = Logger()

@logger.inject_lambda_context
def handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)