import json
from functools import wraps
from aws_lambda_powertools.event_handler import Response
import traceback
from pydantic import ValidationError


def success(data, status_code=200):
    return Response(status_code=status_code, content_type="application/json", body=json.dumps(data))

def error(message, status_code=400):
    return Response(status_code=status_code, content_type="application/json", body=json.dumps({"error": message}))

def handle_errors(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except ValidationError as e:
            return error(e.errors(), status_code=422)
        except ValueError as e:
            return error(str(e), status_code=400)
        except Exception:
            print(traceback.format_exc())
            return error("Internal server error", status_code=500)
    return wrapper