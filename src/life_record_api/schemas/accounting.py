from datetime import date, datetime
from sqlmodel import SQLModel
from fastapi import UploadFile

from life_record_api.models.accounting import RecordType, DurationType, PeriodStatus


class AccountingRecordCreate(SQLModel):
    category_id: int
    amount: int
    note: str | None = None
    expended_at: date
    tags: list[int] = []
    image: UploadFile | None = None


class AccountingRecordUpdate(SQLModel):
    category_id: int | None = None
    amount: int | None = None
    note: str | None = None
    expended_at: date | None = None
    tags: list[int] | None = None
    remove_tags: bool = False
    image: UploadFile | None = None
    remove_image: bool = False


class ImageRead(SQLModel):
    url: str
    name: str


class AccountingRecordRead(SQLModel):
    id: int
    category_id: int
    amount: int
    note: str | None = None
    expended_at: date
    tags: list[int] = []
    image: ImageRead | None = None
    record_type: RecordType


class AccountingRecordDateRange(SQLModel):
    started_at: date
    ended_at: date


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


class PeriodsCreate(SQLModel):
    duration_type: DurationType
    days: int | None = None


class PeriodRead(SQLModel):
    id: int
    duration_type: DurationType
    started_at: datetime
    planned_end_at: datetime
    actual_end_at: datetime | None
    status: PeriodStatus


class GrowingPeriodStatsRead(SQLModel):
    records: list[AccountingRecordRead]
    # dict -> object 的概念
    stats: dict[str, int]
    started_at: datetime
    ended_at: datetime


class StatRead(SQLModel):
    id: int
    name: str
    color: str
