from sqlmodel import Session, select
from fastapi import UploadFile

from life_record_api.models.accounting import (
    AccountingRecords,
    RecordTags,
    TagList,
    RecordImages,
    CategoryList,
    CalcMethod,
)
from life_record_api.exceptions import (
    AppException,
)
from life_record_api.schemas.accounting import (
    AccountingRecordDateRange,
    AccountingRecordCreate,
    AccountingRecordRead,
    ImageRead,
    AccountingRecordUpdate,
    GrowingPeriodStatsRead,
)
from life_record_api.services.storage import upload_image
from life_record_api.services.accounting.periods import (
    get_growing_period_id,
    get_period_days,
)
from life_record_api.services.accounting.stat_list import get_stat_info


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
        session.add(
            RecordImages(record_id=record_id, image_url=url, image_name=image.filename)
        )


def insert_record(session: Session, data: AccountingRecordCreate):
    tag_ids = set(data.tags)

    _validate_tags_exist(session, tag_ids)

    period_id = get_growing_period_id(session)

    # OOO(data) -> 根據 OOO 知道是對哪個表操作
    record = AccountingRecords(
        **data.model_dump(exclude={"tags", "image"}, exclude_none=True),
        period_id=period_id,
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


def _serialize_records(session: Session, records: list) -> list[AccountingRecordRead]:
    # for row in records:
    #     record = row[0]
    #     record_type = row.record_type

    records_ids = [record.id for record, record_type in records]

    tags = session.exec(
        select(RecordTags).where(RecordTags.record_id.in_(records_ids))
    ).all()

    tag_map: dict[int, list[int]] = {}
    for row in tags:
        if row.record_id not in tag_map:
            tag_map[row.record_id] = []
        tag_map[row.record_id].append(row.tag_id)

    images = session.exec(
        select(RecordImages).where(RecordImages.record_id.in_(records_ids))
    ).all()

    image_map: dict[int, ImageRead] = {}
    for row in images:
        image_map[row.record_id] = {"url": row.image_url, "name": row.image_name}

    result = []
    for record, record_type in records:
        result.append(
            {
                **record.model_dump(),
                "tags": tag_map.get(record.id, []),
                "image": image_map.get(record.id),
                "record_type": record_type,
            }
        )
    return result


def read_record_by_date(
    session: Session, data: AccountingRecordDateRange, user_id: int = 0
) -> list[AccountingRecordRead]:
    records = session.exec(
        select(AccountingRecords, CategoryList.type.label("record_type"))
        .join(
            CategoryList, AccountingRecords.category_id == CategoryList.id, isouter=True
        )
        .where(CategoryList.user_id == user_id)
        .where(AccountingRecords.expended_at <= data.ended_at)
        .where(AccountingRecords.expended_at >= data.started_at)
    ).all()

    return _serialize_records(session, records)


def _replace_tags(session: Session, record_id: int, tag_ids: set[int]) -> None:
    existing = session.exec(
        select(RecordTags).where(RecordTags.record_id == record_id)
    ).all()

    for row in existing:
        session.delete(row)
    _attach_tags(session, record_id, tag_ids)


def _replace_image(session: Session, record_id: int, image: UploadFile | None) -> None:
    existing = session.exec(
        select(RecordImages).where(RecordImages.record_id == record_id)
    ).all()
    for row in existing:
        session.delete(row)

    if image is not None:
        _attach_image(session, record_id, image)


def update_record(
    session: Session, record_id: int, data: AccountingRecordUpdate
) -> AccountingRecords:
    # 撈單一一筆，用主鍵查 最簡潔的寫法
    record = session.get(AccountingRecords, record_id)

    if record is None:
        raise AppException(
            status_code=404, error_code="E01003", detail="找不到這筆紀錄"
        )

    # remove_tags=True 代表「明確清空」,跟「這次根本沒傳 tags」要分開判斷
    if data.remove_tags:
        _replace_tags(session, record_id, set())
    elif "tags" in data.model_fields_set:
        tags_ids = set(data.tags or [])
        _validate_tags_exist(session, tags_ids)
        _replace_tags(session, record_id, tags_ids)

    if data.remove_image:
        _replace_image(session, record_id, None)
    elif data.image is not None:
        _replace_image(session, record_id, data.image)

    update_data = data.model_dump(
        exclude_unset=True,
        exclude={"tags", "remove_tags", "image", "remove_image"},
    )
    for key, value in update_data.items():
        # setattr -> 用字串動態指定要改哪個屬性
        setattr(record, key, value)

    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def _read_record_by_growing_status(
    session: Session,
    period_id: int,
    user_id: int = 0,
) -> list[AccountingRecordRead]:
    records = session.exec(
        select(AccountingRecords, CategoryList.type.label("record_type"))
        .join(
            CategoryList, AccountingRecords.category_id == CategoryList.id, isouter=True
        )
        .where(CategoryList.user_id == user_id)
        .where(AccountingRecords.period_id == period_id)
    ).all()

    return _serialize_records(session, records)


def _get_record_by_period_id(session: Session, period_id: int, user_id):
    records = session.exec(
        select(AccountingRecords, CategoryList.add_stats_id)
        .join(
            CategoryList, AccountingRecords.category_id == CategoryList.id, isouter=True
        )
        .where(CategoryList.user_id == user_id)
        .where(AccountingRecords.period_id == period_id)
    ).all()

    results = []
    for record, add_stats_id in records:
        results.append({**record.model_dump(), "add_stats_id": add_stats_id})

    return results


def read_current_growing_slime(
    session: Session, user_id: int = 0
) -> GrowingPeriodStatsRead | None:
    period_id = get_growing_period_id(session, user_id)
    if period_id is None:
        return None

    records = _read_record_by_growing_status(session, period_id, user_id)
    period_day_settings = get_period_days(session, period_id)
    stat = _calculate_stat(
        session, period_id, user_id, days=period_day_settings["days"]
    )

    # 用 schema 包起來 => 會驗證資料格式
    return GrowingPeriodStatsRead(
        records=records,
        stats=stat,
        started_at=period_day_settings["started_at"],
        ended_at=period_day_settings["ended_at"],
    )


def _calculate_stat(session: Session, period_id: int, user_id, days: int):
    records = _get_record_by_period_id(session, period_id, user_id)
    stat_mapping = get_stat_info(session, days)
    stat_summary = {key: 0 for key in stat_mapping}
    for record in records:
        stat_id = record["add_stats_id"]
        info = stat_mapping[stat_id]

        if info["method"] == CalcMethod.count:
            stat_summary[stat_id] = min(stat_summary[stat_id] + 1, info["max"])
        else:
            stat_summary[stat_id] = stat_summary[stat_id] + record["amount"]

    return {
        stat_mapping[stat_id]["name"]: value for stat_id, value in stat_summary.items()
    }
