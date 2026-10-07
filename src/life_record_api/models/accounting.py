from sqlmodel import SQLModel, Field
from enum import Enum
from datetime import date, datetime, timezone


class CalcMethod(str, Enum):
    count = "count"
    amount = "amount"


class StatList(SQLModel, table=True):
    __tablename__ = "stat_list"
    # primary_keys -> unique key
    id: int | None = Field(default=None, primary_key=True)
    name: str
    color: str
    calc_method: CalcMethod


class IconList(SQLModel, table=True):
    __tablename__ = "icon_list"
    id: int | None = Field(default=None, primary_key=True)
    name: str


class RecordType(str, Enum):
    income = "income"
    expense = "expense"


class CategoryList(SQLModel, table=True):
    __tablename__ = "category_list"
    # foreign_key : 外鍵
    id: int | None = Field(default=None, primary_key=True)
    name: str
    icon_id: int = Field(foreign_key="icon_list.id")
    add_stats_id: int = Field(foreign_key="stat_list.id")
    user_id: int = Field(foreign_key="users.id")
    type: RecordType


class AccountingRecords(SQLModel, table=True):
    __tablename__ = "accounting_records"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    category_id: int = Field(foreign_key="category_list.id")
    amount: int
    note: str | None = Field(default=None)
    expended_at: date
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    period_id: int | None = Field(default=None, foreign_key="periods.id")


class DurationType(str, Enum):
    oneday = "oneday"
    twoday = "twoday"
    week = "week"
    month = "month"
    custom = "custom"


class PeriodStatus(str, Enum):
    growing = "growing"
    completed = "completed"


class Periods(SQLModel, table=True):
    __tablename__ = "periods"
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id")
    duration_type: DurationType
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    planned_end_at: datetime
    actual_end_at: datetime | None = Field(default=None)
    status: PeriodStatus


class TagList(SQLModel, table=True):
    __tablename__ = "tag_list"
    id: int | None = Field(default=None, primary_key=True)
    name: str
    color: str
    user_id: int = Field(foreign_key="users.id")


class RecordTags(SQLModel, table=True):
    __tablename__ = "record_tags"
    id: int | None = Field(default=None, primary_key=True)
    tag_id: int = Field(foreign_key="tag_list.id")
    record_id: int = Field(foreign_key="accounting_records.id")


class RecordImages(SQLModel, table=True):
    __tablename__ = "record_images"
    id: int | None = Field(default=None, primary_key=True)
    image_url: str
    record_id: int = Field(foreign_key="accounting_records.id")
    image_name: str


class ProfessionType(str, Enum):
    warrior = "warrior"
    bowman = "bowman"
    thief = "thief"
    wizard = "wizard"
    paladin = "paladin"


class Slimes(SQLModel, table=True):
    __tablename__ = "slimes"
    id: int | None = Field(default=None, primary_key=True)
    period_id: int = Field(foreign_key="periods.id")
    user_id: int = Field(foreign_key="users.id")
    power: int
    agility: int
    luck: int
    intelligence: int
    stamina: int
    wealth: int
    profession: ProfessionType
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
