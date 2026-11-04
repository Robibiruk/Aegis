import time

from apps.api.db import SessionLocal
from apps.api.reminders import LogNotificationSender, process_due_reminders


def run_forever(interval_seconds: int = 30) -> None:
    sender = LogNotificationSender()
    print(f"[aegis] reminder worker started; polling every {interval_seconds}s")
    while True:
        with SessionLocal() as db:
            delivered = process_due_reminders(db, sender)
        if delivered:
            print(f"[aegis] delivered {delivered} reminder(s)")
        time.sleep(interval_seconds)


if __name__ == "__main__":
    run_forever()
