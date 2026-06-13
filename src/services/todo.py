import os
import json
import uuid
import boto3
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from src.repositories import todo as todo_repo
from src.schemas.todo import CreateTodoRequest, UpdateTodoRequest
from src.models.todo import Todo
from src.constants.todo import TodoStatus, RecurrencePattern, ScheduleAction

# Note: monthly/quarterly/semi_annual/annual recurrences chain off the previous
# occurrence date, so day-of-month may drift downward (toward 28) when passing
# through shorter months (e.g. Jan 31 -> Feb 28 -> Mar 28, not Mar 31). This is
# a one-way, bounded drift (floor of 28) and is accepted behavior.
RECURRENCE_MAP = {
    RecurrencePattern.daily: lambda dt: dt + timedelta(days=1),
    RecurrencePattern.weekly: lambda dt: dt + timedelta(weeks=1),
    RecurrencePattern.monthly: lambda dt: dt + relativedelta(months=1),
    RecurrencePattern.quarterly: lambda dt: dt + relativedelta(months=3),
    RecurrencePattern.semi_annual: lambda dt: dt + relativedelta(months=6),
    RecurrencePattern.annual: lambda dt: dt + relativedelta(years=1),
}

_CHILD_EDITABLE_FIELDS = {"title", "body", "status"}

_scheduler_client = None


def _get_scheduler_client():
    global _scheduler_client
    if _scheduler_client is None:
        _scheduler_client = boto3.client(
            "scheduler", region_name=os.environ.get("AWS_DEFAULT_REGION", "ap-southeast-1")
        )
    return _scheduler_client


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
        next_occurrence_at=body.next_occurrence_at,
        notify=body.notify,
        notify_at=body.notify_at,
        notify_sms=body.notify_sms,
        notify_web=body.notify_web,
        created_at=now,
        updated_at=now,
    )
    todo_repo.save(item)
    if body.notify and body.notify_at:
        _create_schedule(ScheduleAction.notify.value, item.id, body.notify_at)
    if body.is_recurring and body.next_occurrence_at:
        _create_schedule(ScheduleAction.recur.value, item.id, body.next_occurrence_at)
    return item

def update(id: str, body: UpdateTodoRequest):
    existing = todo_repo.find_by_id(id)
    if not existing:
        raise ValueError("Todo not found")
    now = datetime.now(timezone.utc).isoformat()
    updates = {k: v for k, v in body.model_dump(mode="json").items() if v is not None}
    updates["updated_at"] = now

    if existing.get("recurring_parent_id"):
        # Child record: only title/body/status are editable, scheduler untouched
        updates = {k: v for k, v in updates.items() if k in _CHILD_EDITABLE_FIELDS}
        return todo_repo.update(id, updates)

    # Notification schedule (independent of recurrence)
    notify = updates.get("notify", existing.get("notify"))
    notify_at = updates.get("notify_at", existing.get("notify_at"))
    if not notify and existing.get("notify"):
        _delete_schedule(ScheduleAction.notify.value, id)
    elif notify and notify_at and (not existing.get("notify") or "notify_at" in updates):
        _delete_schedule(ScheduleAction.notify.value, id)
        _create_schedule(ScheduleAction.notify.value, id, notify_at)

    # Recurrence schedule (independent of notification)
    is_recurring = updates.get("is_recurring", existing.get("is_recurring"))
    next_occurrence_at = updates.get("next_occurrence_at", existing.get("next_occurrence_at"))
    if not is_recurring and existing.get("is_recurring"):
        _delete_schedule(ScheduleAction.recur.value, id)
    elif is_recurring and next_occurrence_at and (not existing.get("is_recurring") or "next_occurrence_at" in updates):
        _delete_schedule(ScheduleAction.recur.value, id)
        _create_schedule(ScheduleAction.recur.value, id, next_occurrence_at)

    return todo_repo.update(id, updates)

def delete(id: str):
    existing = todo_repo.find_by_id(id)
    if not existing:
        raise ValueError("Todo not found")
    if not existing.get("recurring_parent_id"):
        if existing.get("notify"):
            _delete_schedule(ScheduleAction.notify.value, id)
        if existing.get("is_recurring"):
            _delete_schedule(ScheduleAction.recur.value, id)
    todo_repo.delete(id)

def handle_recurrence(todo: dict):
    try:
        recurrence = RecurrencePattern(todo["recurrence"])
    except (ValueError, KeyError):
        print(f"[WARN] Invalid recurrence for todo {todo['id']}, skipping recurrence")
        return

    now = datetime.now(timezone.utc).isoformat()

    # Snapshot current state into a new history record
    snapshot_data = {**todo}
    snapshot_data["id"] = str(uuid.uuid4())
    snapshot_data["recurring_parent_id"] = todo["id"]
    snapshot_data["created_at"] = now
    snapshot_data["updated_at"] = now
    snapshot_data["ttl"] = None
    todo_repo.save(Todo(**snapshot_data))

    # Reset template: advance next_occurrence_at, back to pending
    next_occ = RECURRENCE_MAP[recurrence](datetime.fromisoformat(todo["next_occurrence_at"]))
    updates = {
        "status": TodoStatus.pending.value,
        "next_occurrence_at": next_occ.isoformat(),
        "updated_at": now,
    }

    # Advance notify_at by the same interval, only if notify was set
    if todo.get("notify") and todo.get("notify_at"):
        next_notify = RECURRENCE_MAP[recurrence](datetime.fromisoformat(todo["notify_at"]))
        updates["notify_at"] = next_notify.isoformat()

    todo_repo.update(todo["id"], updates)

    # Reschedule recurrence for the next cycle
    _delete_schedule(ScheduleAction.recur.value, todo["id"])
    _create_schedule(ScheduleAction.recur.value, todo["id"], updates["next_occurrence_at"])

    # Reschedule notification for the next cycle, if applicable
    _delete_schedule(ScheduleAction.notify.value, todo["id"])
    if todo.get("notify") and updates.get("notify_at"):
        _create_schedule(ScheduleAction.notify.value, todo["id"], updates["notify_at"])

def _schedule_name(action: str, todo_id: str) -> str:
    return f"todo-{action}-{todo_id}"

def _create_schedule(action: str, todo_id: str, at: str):
    if os.environ.get("APP_ENV") == "local":
        print(f"[LOCAL SCHEDULE] Create {action} schedule for todo {todo_id} at {at}")
        return
    scheduler = _get_scheduler_client()
    dt = datetime.fromisoformat(at).replace(tzinfo=None)
    scheduler.create_schedule(
        Name=_schedule_name(action, todo_id),
        ScheduleExpression=f"at({dt.strftime('%Y-%m-%dT%H:%M:%S')})",
        ScheduleExpressionTimezone="UTC",
        Target={
            "Arn": os.environ["NOTIFICATION_FUNCTION_ARN"],
            "RoleArn": os.environ["SCHEDULER_ROLE_ARN"],
            "Input": json.dumps({"todo_id": todo_id, "action": action})
        },
        FlexibleTimeWindow={"Mode": "OFF"},
        ActionAfterCompletion="DELETE"
    )

def _delete_schedule(action: str, todo_id: str):
    if os.environ.get("APP_ENV") == "local":
        print(f"[LOCAL SCHEDULE] Delete {action} schedule for todo {todo_id}")
        return
    try:
        scheduler = _get_scheduler_client()
        scheduler.delete_schedule(Name=_schedule_name(action, todo_id))
    except scheduler.exceptions.ResourceNotFoundException:
        pass