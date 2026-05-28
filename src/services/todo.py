import uuid
from datetime import datetime, timezone
from src.repositories import todo as todo_repo
from src.schemas.todo import CreateTodoRequest, UpdateTodoRequest
from src.models.todo import Todo
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta

def list_all(limit: int = 10, cursor: dict = None):
    return todo_repo.find_all(limit=limit, cursor=cursor)

def get_by_id(id: str):
    item = todo_repo.find_by_id(id)
    if not item:
        raise ValueError("Todo not found")
    return item

def create(body: CreateTodoRequest):
    now = datetime.now(timezone.utc).isoformat()
    item = Todo(
        id=str(uuid.uuid4()),
        title=body.title,
        body=body.body,
        status="pending",
        is_recurring=body.is_recurring,
        recurrence=body.recurrence,
        notify=body.notify,
        notify_at=body.notify_at,
        notify_sms=body.notify_sms,
        notify_web=body.notify_web,
        created_at=now,
        updated_at=now,
    )
    todo_repo.save(item)
    return item

def update(id: str, body: UpdateTodoRequest):
    existing = todo_repo.find_by_id(id)
    if not existing:
        raise ValueError("Todo not found")
    now = datetime.now(timezone.utc).isoformat()
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    updates["updated_at"] = now
    todo_repo.update(id, updates)
    return {**existing, **updates}

def delete(id: str):
    existing = todo_repo.find_by_id(id)
    if not existing:
        raise ValueError("Todo not found")
    todo_repo.delete(id)

RECURRENCE_MAP = {
    "daily": lambda dt: dt + timedelta(days=1),
    "weekly": lambda dt: dt + timedelta(weeks=1),
    "monthly": lambda dt: dt + relativedelta(months=1),
    "quarterly": lambda dt: dt + relativedelta(months=3),
    "semi-annual": lambda dt: dt + relativedelta(months=6),
    "annual": lambda dt: dt + relativedelta(years=1),
}

def process_notifications():
    from src.repositories import todo as todo_repo
    from src.services import notification as notification_service
    todos = todo_repo.find_pending_notifications()
    for todo in todos:
        notification_service.notify(todo)
        if todo.get("is_recurring") and todo.get("recurrence"):
            _reschedule(todo)

def _reschedule(todo: dict):
    from src.repositories import todo as todo_repo
    recurrence = todo["recurrence"]
    current_notify_at = datetime.fromisoformat(todo["notify_at"])
    next_notify_at = RECURRENCE_MAP[recurrence](current_notify_at)
    todo_repo.update(todo["id"], {
        "notify_at": next_notify_at.isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    })