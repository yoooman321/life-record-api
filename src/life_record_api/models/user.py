from sqlmodel import SQLModel, Field
from datetime import date, datetime, timezone


class Users(SQLModel, table=True):
    __tablename__ = "users"
    id: int | None = Field(default=None, primary_key=True)
    name: str | None = Field(default=None)
    email: str = Field(unique=True, index=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    birthday: date | None = Field(default=None)
