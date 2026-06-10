import json

def parse_int(value, default: int, min_val: int = 1, max_val: int = 100) -> int:
    try:
        result = int(value)
        return max(min_val, min(max_val, result))  # clamps between min and max
    except (ValueError, TypeError):
        return default

def parse_cursor(value) -> dict | None:
    try:
        return json.loads(value) if value else None
    except json.JSONDecodeError:
        return None

def parse_str(value, default: str = None) -> str | None:
    if not value:
        return default
    return str(value).strip()