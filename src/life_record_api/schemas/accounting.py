from datetime import date
from sqlmodel import SQLModel
from fastapi import UploadFile

from life_record_api.models.accounting import RecordType


class AccountingRecordCreate(SQLModel):
    category_id: int
    amount: int
    note: str | None = None
    expended_at: date
    tags: list[int] = []
    image: UploadFile | None = None


class CategoryRead(SQLModel):
    id: int
    name: str
    icon_id: int
    add_stats_id: int
    user_id: int
    type: RecordType
    color: str | None = None


class TagCreate(SQLModel):
    name: str
    color: str


class TagRead(SQLModel):
    id: int
    name: str
    color: str
