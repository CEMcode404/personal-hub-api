from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from src.repositories import connection as connection_repo

logger = Logger()

@logger.inject_lambda_context
def handler(event: dict, context: LambdaContext) -> dict:
    route_key = event.get("requestContext", {}).get("routeKey")
    connection_id = event.get("requestContext", {}).get("connectionId")

    if route_key == "$connect":
        connection_repo.save(connection_id)
        logger.info(f"Client connected: {connection_id}")
        return {"statusCode": 200, "body": "Connected"}

    elif route_key == "$disconnect":
        connection_repo.delete(connection_id)
        logger.info(f"Client disconnected: {connection_id}")
        return {"statusCode": 200, "body": "Disconnected"}

    else:
        logger.info(f"Default route: {connection_id}")
        return {"statusCode": 200, "body": "OK"}