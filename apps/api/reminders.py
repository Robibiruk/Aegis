from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import DeliveryAttempt, Reminder, ReminderStatus, Task, TaskStatus


class NotificationSender(Protocol):
    def send(self, task: Task) -> None: ...


class LogNotificationSender:
    def send(self, task: Task) -> None:
        print(f"[aegis] reminder due: {task.title} ({task.id})")


def schedule_reminder(db: Session, task: Task) -> Reminder | None:
    if task.due_at is None:
        return None
    scheduled_for = task.due_at.astimezone(UTC)
    existing = db.scalar(
        select(Reminder).where(Reminder.task_id == task.id, Reminder.scheduled_for == scheduled_for)
    )
    if existing:
        return existing
    reminder = Reminder(
        task_id=task.id,
        scheduled_for=scheduled_for,
        idempotency_key=f"task:{task.id}:due:{scheduled_for.isoformat()}",
    )
    db.add(reminder)
    db.flush()
    return reminder


def cancel_pending_reminders(db: Session, task: Task) -> None:
    for reminder in task.reminders:
        if reminder.status == ReminderStatus.PENDING.value:
            reminder.status = ReminderStatus.CANCELLED.value


def process_due_reminders(
    db: Session,
    sender: NotificationSender,
    now: datetime | None = None,
) -> int:
    now = (now or datetime.now(UTC)).astimezone(UTC)
    reminders = db.scalars(
        select(Reminder)
        .where(Reminder.status == ReminderStatus.PENDING.value, Reminder.scheduled_for <= now)
        .with_for_update()
    ).all()
    delivered = 0
    for reminder in reminders:
        task = db.get(Task, reminder.task_id)
        if not task or task.status != TaskStatus.OPEN.value:
            reminder.status = ReminderStatus.CANCELLED.value
            continue
        attempt_key = f"{reminder.idempotency_key}:attempt:{reminder.attempt_count + 1}"
        if db.scalar(select(DeliveryAttempt).where(DeliveryAttempt.idempotency_key == attempt_key)):
            continue
        reminder.attempt_count += 1
        try:
            sender.send(task)
        except Exception as exc:
            reminder.last_error = str(exc)
            db.add(
                DeliveryAttempt(
                    reminder_id=reminder.id,
                    idempotency_key=attempt_key,
                    outcome="failed",
                    error=str(exc),
                )
            )
        else:
            reminder.status = ReminderStatus.SENT.value
            db.add(
                DeliveryAttempt(
                    reminder_id=reminder.id,
                    idempotency_key=attempt_key,
                    outcome="sent",
                )
            )
            delivered += 1
    db.commit()
    return delivered
