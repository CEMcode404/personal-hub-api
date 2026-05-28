import os
import boto3

_dynamodb = None

def get_dynamodb():
    global _dynamodb
    if _dynamodb is None:
        endpoint = os.environ.get("DYNAMODB_ENDPOINT_URL")
        print("ENDPOINT:", endpoint)
        _dynamodb = boto3.resource("dynamodb", endpoint_url=endpoint)
    return _dynamodb

def get_table(name: str):
    return get_dynamodb().Table(name)