from sqlmodel import Session, select
from fastapi import UploadFile

from life_record_api.models.accounting import (
    AccountingRecords,
    RecordTags,
    TagList,
    RecordImages,
)
from life_record_api.exceptions import (
    AppException,
)
from life_record_api.schemas.accounting import AccountingRecordCreate
from life_record_api.services.storage import upload_image


def _validate_tags_exist(session: Session, tag_ids: set[int]) -> None:
    if not tag_ids:
        return
    statement = select(TagList.id).where(TagList.id.in_(tag_ids))
    found_ids = set(session.exec(statement).all())
    # 相扣重複的
    missing = tag_ids - found_ids
    if missing:
        raise AppException(
            status_code=404,
            error_code="E01004",
            detail=f"找不到標籤: {sorted(missing)}",
        )


def _attach_tags(session: Session, record_id: int, tag_ids: set[int]) -> None:
    session.add_all(
        RecordTags(record_id=record_id, tag_id=tag_id) for tag_id in tag_ids
    )


def _attach_image(session: Session, record_id: int, image: UploadFile | None) -> None:
    if image is not None:
        url = upload_image(image)
        session.add(RecordImages(record_id=record_id, image_url=url))


def insert_record(session: Session, data: AccountingRecordCreate):
    tag_ids = set(data.tags)

    _validate_tags_exist(session, tag_ids)

    # OOO(data) -> 根據 OOO 知道是對哪個表操作
    record = AccountingRecords(
        **data.model_dump(exclude={"tags", "image"}, exclude_none=True)
    )
    session.add(record)
    # session.flush - 先拿到 record.id, 還沒結帳
    session.flush()

    _attach_image(session, record_id=record.id, image=data.image)

    # 插入多欄
    # set() -> 跟 js 的 new Set() 一樣
    _attach_tags(session, record_id=record.id, tag_ids=tag_ids)

    # 最後一起 執行
    session.commit()
    session.refresh(record)

    return record
