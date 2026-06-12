def clean_internal_fields(item: dict, internal_fields: set[str]) -> dict:
    return {k: v for k, v in item.items() if k not in internal_fields}