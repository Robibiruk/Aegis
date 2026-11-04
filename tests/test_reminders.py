from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.db import Base
from apps.api.models import Task, TaskStatus, User
from apps.api.reminders import process_due_reminders, schedule_reminder


class Sender:
    def __init__(self):
        self.sent = []

    def send(self, task):
        self.sent.append(task.id)


def test_due_reminder_is_delivered_once_and_completed_task_is_cancelled(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'reminders.db'}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    user = User(email="reminders@example.com", password_hash="hash")
    session.add(user)
    session.flush()
    task = Task(
        user_id=user.id,
        title="Send application",
        due_at=datetime.now(UTC) - timedelta(minutes=1),
        timezone="UTC",
    )
    session.add(task)
    session.flush()
    reminder = schedule_reminder(session, task)
    session.commit()

    sender = Sender()
    assert process_due_reminders(session, sender) == 1
    assert process_due_reminders(session, sender) == 0
    assert sender.sent == [task.id]
    assert reminder.status == "sent"

    pending_task = Task(
        user_id=user.id,
        title="Do not send",
        due_at=datetime.now(UTC) - timedelta(minutes=1),
        timezone="UTC",
        status=TaskStatus.COMPLETED.value,
    )
    session.add(pending_task)
    session.flush()
    cancelled = schedule_reminder(session, pending_task)
    session.commit()
    assert process_due_reminders(session, sender) == 0
    assert cancelled.status == "cancelled"
