from typing import Annotated
from fastapi import APIRouter, Depends, Form
from sqlmodel import Session

from life_record_api.models.accounting import AccountingRecords, IconList, TagList
from life_record_api.db.session import get_session
from life_record_api.schemas.accounting import (
    AccountingRecordCreate,
    CategoryRead,
    TagCreate,
    TagRead,
)

from life_record_api.services.accounting.icon import get_icon_list
from life_record_api.services.accounting.category import get_category_list
from life_record_api.services.accounting.tags import get_tag_list, insert_tag
from life_record_api.services.accounting.records import insert_record

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
