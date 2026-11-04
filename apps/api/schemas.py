from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from .models import TaskStatus


class AuthInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    notes: str | None = Field(default=None, max_length=10_000)
    due_at: datetime | None = None
    timezone: str = Field(default="UTC", min_length=1, max_length=64)

    @field_validator("due_at")
    @classmethod
    def require_aware_due_at(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("due_at must include a timezone offset")
        return value


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    notes: str | None = Field(default=None, max_length=10_000)
    due_at: datetime | None = None
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    status: TaskStatus | None = None

    @field_validator("due_at")
    @classmethod
    def require_aware_due_at(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("due_at must include a timezone offset")
        return value


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    notes: str | None
    due_at: datetime | None
    timezone: str
    status: str


class ReminderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    scheduled_for: datetime
    status: str
    attempt_count: int
    last_error: str | None


class SourceCreate(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    title: str | None = Field(default=None, max_length=240)


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    canonical_url: str
    title: str | None
    status: str
    captured_at: datetime
