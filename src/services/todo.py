import os
import uuid
import boto3
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from src.repositories import todo as todo_repo
from src.schemas.todo import CreateTodoRequest, UpdateTodoRequest
from src.models.todo import Todo
from src.services import notification as notification_service
from src.constants.todo import TodoStatus, RecurrencePattern

RECURRENCE_MAP = {
    RecurrencePattern.daily: lambda dt: dt + timedelta(days=1),
    RecurrencePattern.weekly: lambda dt: dt + timedelta(weeks=1),
    RecurrencePattern.monthly: lambda dt: dt + relativedelta(months=1),
    RecurrencePattern.quarterly: lambda dt: dt + relativedelta(months=3),
    RecurrencePattern.semi_annual: lambda dt: dt + relativedelta(months=6),
    RecurrencePattern.annual: lambda dt: dt + relativedelta(years=1),
}

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
        status=TodoStatus.pending,
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
    if body.notify and body.notify_at:
        _create_schedule(item.id, body.notify_at)
    return item

def update(id: str, body: UpdateTodoRequest):
    existing = todo_repo.find_by_id(id)
    if not existing:
        raise ValueError("Todo not found")
    now = datetime.now(timezone.utc).isoformat()
    updates = {k: v for k, v in body.model_dump(mode="json").items() if v is not None}
    updates["updated_at"] = now

    notify = updates.get("notify", existing.get("notify"))
    notify_at = updates.get("notify_at", existing.get("notify_at"))

    if not notify and existing.get("notify"):
        _delete_schedule(id)
    elif notify and notify_at and (not existing.get("notify") or "notify_at" in updates):
        _delete_schedule(id)
        _create_schedule(id, notify_at)

    return todo_repo.update(id, updates)

def delete(id: str):
    existing = todo_repo.find_by_id(id)
    if not existing:
        raise ValueError("Todo not found")
    if existing.get("notify"):
        _delete_schedule(id)
    todo_repo.delete(id)

def process_notification(todo_id: str):
    todo = todo_repo.find_by_id(todo_id)
    if not todo:
        print(f"[WARN] Todo {todo_id} not found for notification processing")
        return
    notification_service.notify(todo)
    if todo.get("is_recurring") and todo.get("recurrence"):
        _reschedule(todo)

def _reschedule(todo: dict):
    try:
        recurrence = RecurrencePattern(todo["recurrence"])
    except ValueError:
        print(f"[WARN] Unknown recurrence pattern '{todo['recurrence']}' for todo {todo['id']}, skipping reschedule")
        return
    current_notify_at = datetime.fromisoformat(todo["notify_at"])
    next_notify_at = RECURRENCE_MAP[recurrence](current_notify_at)
    next_notify_at_str = next_notify_at.isoformat()
    todo_repo.update(todo["id"], {
        "notify_at": next_notify_at_str,
        "updated_at": datetime.now(timezone.utc).isoformat()
    })
    _delete_schedule(todo["id"])
    _create_schedule(todo["id"], next_notify_at_str)

def _create_schedule(todo_id: str, notify_at: str):
    if os.environ.get("APP_ENV") == "local":
        print(f"[LOCAL SCHEDULE] Create schedule for todo {todo_id} at {notify_at}")
        return
    scheduler = boto3.client("scheduler", region_name=os.environ.get("AWS_DEFAULT_REGION", "ap-southeast-1"))
    dt = datetime.fromisoformat(notify_at).replace(tzinfo=None)
    scheduler.create_schedule(
        Name=f"todo-{todo_id}",
        ScheduleExpression=f"at({dt.strftime('%Y-%m-%dT%H:%M:%S')})",
        ScheduleExpressionTimezone="UTC",
        Target={
            "Arn": os.environ["NOTIFICATION_FUNCTION_ARN"],
            "RoleArn": os.environ["SCHEDULER_ROLE_ARN"],
            "Input": f'{{"todo_id": "{todo_id}"}}'
        },
        FlexibleTimeWindow={"Mode": "OFF"},
        ActionAfterCompletion="DELETE"
    )

def _delete_schedule(todo_id: str):
    if os.environ.get("APP_ENV") == "local":
        print(f"[LOCAL SCHEDULE] Delete schedule for todo {todo_id}")
        return
    try:
        scheduler = boto3.client("scheduler", region_name=os.environ.get("AWS_DEFAULT_REGION", "ap-southeast-1"))
        scheduler.delete_schedule(Name=f"todo-{todo_id}")
    except scheduler.exceptions.ResourceNotFoundException:
        pass