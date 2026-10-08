from typing import Annotated
from fastapi import APIRouter, Depends, Form, Query
from sqlmodel import Session
from life_record_api.exceptions import AppException

from life_record_api.models.accounting import AccountingRecords, IconList, Slimes
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
    SlimeEdit,
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
    get_growing_period,
)

from life_record_api.services.accounting.stat_list import (
    get_stat_list,
)
from life_record_api.services.users import get_current_user

from life_record_api.services.accounting.slime import insert_slime, update_slime

router = APIRouter(
    prefix="/accounting", tags=["accounting"], dependencies=[Depends(get_current_user)]
)


# record
@router.post("/record", response_model=AccountingRecords)
def create_record(
    # 告訴 FastAPI 這個 model 是從表單欄位來的 用 Form() 標記
    # Annotated: 在原本的型別上，多附上一些額外資訊，但型別本身不變
    data: Annotated[AccountingRecordCreate, Form()],
    session: Session = Depends(get_session),
    user_id: int = Depends(get_current_user),
):
    return insert_record(session, data, user_id)


@router.get("/records", response_model=list[AccountingRecordRead])
def list_records(
    data: Annotated[AccountingRecordDateRange, Query()],
    session: Session = Depends(get_session),
    user_id: int = Depends(get_current_user),
):
    return read_record_by_date(session, data, user_id)


@router.get("/records/current-period", response_model=GrowingPeriodStatsRead | None)
def list_current_period_records(
    session: Session = Depends(get_session), user_id: int = Depends(get_current_user)
):
    return read_current_growing_slime(session, user_id)


@router.put("/record/{record_id}", response_model=AccountingRecords)
def edit_records(
    record_id: int,
    data: Annotated[AccountingRecordUpdate, Form()],
    session: Session = Depends(get_session),
    user_id: int = Depends(get_current_user),
):
    return update_record(session, record_id, data, user_id)


# icon
@router.get("/icons", response_model=list[IconList])
def list_icons(session: Session = Depends(get_session)):
    return get_icon_list(session)


# category
@router.get("/categories", response_model=list[CategoryRead])
def list_categories(
    session: Session = Depends(get_session), user_id: int = Depends(get_current_user)
):
    return get_category_list(session, user_id)


# tags
@router.get("/tags", response_model=list[TagRead])
def list_tags(
    session: Session = Depends(get_session), user_id: int = Depends(get_current_user)
):
    return get_tag_list(session, user_id)


@router.post("/tags", response_model=TagRead)
def create_tag(
    data: TagCreate,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_current_user),
):
    return insert_tag(session, data, user_id)


# period
@router.post("/period", response_model=PeriodRead)
def create_period(
    data: PeriodsCreate,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_current_user),
):
    return insert_period(session, data, user_id)


@router.put("/period/current/end", response_model=Slimes)
def end_current_period(
    session: Session = Depends(get_session), user_id: int = Depends(get_current_user)
):
    period = get_growing_period(session, user_id)
    if period is None:
        raise AppException(
            status_code=404, error_code="E01002", detail="目前沒有正在培育的史萊姆"
        )
    return insert_slime(session, period, user_id)


# stat
@router.get("/stat", response_model=list[StatRead])
def list_stat_list(session: Session = Depends(get_session)):
    return get_stat_list(session)


# slime
@router.put("/slime", response_model=Slimes)
def edit_slime(
    data: SlimeEdit,
    session: Session = Depends(get_session),
    user_id: int = Depends(get_current_user),
):
    return update_slime(session, data, user_id)
