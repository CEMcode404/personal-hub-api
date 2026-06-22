import os
import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from repositories import connection as connection_repo

logger = Logger()

def authorizer(event: dict, context: LambdaContext) -> dict:
    token = event.get("queryStringParameters", {}).get("token")
    method_arn = event.get("methodArn")
    
    if not token:
        return _deny("anonymous", method_arn)
    
    try:
        client = boto3.client("cognito-idp", region_name=os.environ.get("AWS_DEFAULT_REGION"))
        user = client.get_user(AccessToken=token)
        return _allow(user["Username"], method_arn)
    except Exception:
        return _deny("anonymous", method_arn)

def _allow(principal_id: str, method_arn: str) -> dict:
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{
                "Action": "execute-api:Invoke",
                "Effect": "Allow",
                "Resource": method_arn
            }]
        }
    }

def _deny(principal_id: str, method_arn: str) -> dict:
    return {
        "principalId": principal_id,
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{
                "Action": "execute-api:Invoke",
                "Effect": "Deny",
                "Resource": method_arn
            }]
        }
    }

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
        return {"statusCode": 200, "body": "OK"}