from typing import Annotated
from fastapi import APIRouter, Depends, Form, Query
from sqlmodel import Session

from life_record_api.models.accounting import AccountingRecords, IconList
from life_record_api.db.session import get_session
from life_record_api.schemas.accounting import (
    AccountingRecordCreate,
    CategoryRead,
    TagCreate,
    TagRead,
    AccountingRecordRead,
    AccountingRecordDateRange,
    AccountingRecordUpdate,
    PeriodsCreate,
    PeriodRead,
    GrowingPeriodStatsRead,
    StatRead,
)

from life_record_api.services.accounting.icon import get_icon_list
from life_record_api.services.accounting.category import get_category_list
from life_record_api.services.accounting.tags import get_tag_list, insert_tag
from life_record_api.services.accounting.records import (
    insert_record,
    read_record_by_date,
    update_record,
    read_current_growing_slime,
)
from life_record_api.services.accounting.periods import (
    insert_period,
    end_growing_period,
)

from life_record_api.services.accounting.stat_list import (
    get_stat_list,
)


router = APIRouter(prefix="/accounting", tags=["accounting"])


# record
@router.post("/record", response_model=AccountingRecords)
def create_record(
    # 告訴 FastAPI 這個 model 是從表單欄位來的 用 Form() 標記
    # Annotated: 在原本的型別上，多附上一些額外資訊，但型別本身不變
    data: Annotated[AccountingRecordCreate, Form()],
    session: Session = Depends(get_session),
):
    return insert_record(session, data)


@router.get("/records", response_model=list[AccountingRecordRead])
def list_records(
    data: Annotated[AccountingRecordDateRange, Query()],
    session: Session = Depends(get_session),
):
    return read_record_by_date(session, data)


@router.get("/records/current-period", response_model=GrowingPeriodStatsRead | None)
def list_current_period_records(
    session: Session = Depends(get_session),
):
    return read_current_growing_slime(session)


@router.put("/record/{record_id}", response_model=AccountingRecords)
def edit_records(
    record_id: int,
    data: Annotated[AccountingRecordUpdate, Form()],
    session: Session = Depends(get_session),
):
    return update_record(session, record_id, data)


# icon
@router.get("/icons", response_model=list[IconList])
def list_icons(session: Session = Depends(get_session)):
    return get_icon_list(session)


# category
@router.get("/categories", response_model=list[CategoryRead])
def list_categories(session: Session = Depends(get_session)):
    return get_category_list(session)


# tags
@router.get("/tags", response_model=list[TagRead])
def list_tags(session: Session = Depends(get_session)):
    return get_tag_list(session)


@router.post("/tags", response_model=TagRead)
def create_tag(data: TagCreate, session: Session = Depends(get_session)):
    return insert_tag(session, data)


# period
@router.post("/period", response_model=PeriodRead)
def create_period(data: PeriodsCreate, session: Session = Depends(get_session)):
    return insert_period(session, data)


@router.put("/period/current/end", response_model=PeriodRead)
def end_current_period(session: Session = Depends(get_session)):
    return end_growing_period(session)


# stat
@router.get("/stat", response_model=list[StatRead])
def list_stat_list(session: Session = Depends(get_session)):
    return get_stat_list(session)
