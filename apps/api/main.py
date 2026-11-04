from datetime import UTC, datetime
from urllib.parse import urlparse, urlunparse

from fastapi import Depends, FastAPI, Header, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import get_settings
from .db import Base, engine, get_db
from .models import Reminder, SourceRecord, Task, TaskStatus, User
from .reminders import schedule_reminder
from .schemas import (
    AuthInput,
    AuthResponse,
    ReminderResponse,
    SourceCreate,
    SourceResponse,
    TaskCreate,
    TaskResponse,
    TaskUpdate,
)
from .security import create_session, get_user_for_token, hash_password, verify_password

Base.metadata.create_all(bind=engine)
settings = get_settings()
app = FastAPI(title="Aegis API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> User:
    scheme, _, token = (authorization or "").partition(" ")
    user = get_user_for_token(db, token if scheme.lower() == "bearer" else None)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: AuthInput, db: Session = Depends(get_db)) -> AuthResponse:
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    return AuthResponse(access_token=create_session(db, user))


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: AuthInput, db: Session = Depends(get_db)) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return AuthResponse(access_token=create_session(db, user))


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Task:
    task = Task(
        user_id=user.id,
        title=payload.title.strip(),
        notes=payload.notes,
        due_at=payload.due_at,
        timezone=payload.timezone,
    )
    db.add(task)
    db.flush()
    schedule_reminder(db, task)
    db.commit()
    db.refresh(task)
    return task


@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[Task]:
    return list(
        db.scalars(select(Task).where(Task.user_id == user.id).order_by(Task.due_at.is_(None), Task.due_at)).all()
    )


@app.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    payload: TaskUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> Task:
    task = db.scalar(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    changed_schedule = payload.due_at is not None and payload.due_at != task.due_at
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value.value if isinstance(value, TaskStatus) else value)
    if task.status in (TaskStatus.COMPLETED.value, TaskStatus.CANCELLED.value) or changed_schedule:
        for reminder in task.reminders:
            if reminder.status == "pending":
                reminder.status = "cancelled"
        if task.status == TaskStatus.OPEN.value:
            schedule_reminder(db, task)
    db.commit()
    db.refresh(task)
    return task


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)) -> Response:
    task = db.scalar(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/reminders", response_model=list[ReminderResponse])
def list_reminders(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[Reminder]:
    return list(
        db.scalars(
            select(Reminder).join(Task).where(Task.user_id == user.id).order_by(Reminder.scheduled_for)
        ).all()
    )


@app.post("/sources", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
def capture_source(
    payload: SourceCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> SourceRecord:
    parsed = urlparse(payload.url.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="A valid HTTP(S) URL is required")
    canonical_url = urlunparse((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or "/", "", parsed.query, ""))
    existing = db.scalar(
        select(SourceRecord).where(SourceRecord.user_id == user.id, SourceRecord.canonical_url == canonical_url)
    )
    if existing:
        return existing
    source = SourceRecord(user_id=user.id, canonical_url=canonical_url, title=payload.title)
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@app.get("/sources", response_model=list[SourceResponse])
def list_sources(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[SourceRecord]:
    return list(
        db.scalars(select(SourceRecord).where(SourceRecord.user_id == user.id).order_by(SourceRecord.captured_at.desc())).all()
    )
