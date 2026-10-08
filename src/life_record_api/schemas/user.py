from sqlmodel import SQLModel
from datetime import date


class UserCreate(SQLModel):
    email: str
    password: str
    birthday: date | None = None
    name: str


class UserRead(SQLModel):
    access_token: str


class UserLogin(SQLModel):
    email: str
    password: str
