from sqlmodel import Session, select
from life_record_api.models.accounting import RecordType, CategoryList, StatList
from life_record_api.schemas.accounting import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    CategoryOrderUpdate,
)
from life_record_api.exceptions import (
    AppException,
)
from life_record_api.services.accounting.icon import validate_icon_id
from life_record_api.services.accounting.stat_list import validate_stat_list

DEFAULT_CATEGORIES = [
    {
        "name": "食物",
        "icon_id": 1,
        "add_stats_id": 1,
        "type": RecordType.expense,
        "sort_order": 0,
    },
    {
        "name": "點心",
        "icon_id": 139,
        "add_stats_id": 1,
        "type": RecordType.expense,
        "sort_order": 1,
    },
    {
        "name": "飲料",
        "icon_id": 7,
        "add_stats_id": 1,
        "type": RecordType.expense,
        "sort_order": 2,
    },
    {
        "name": "交通",
        "icon_id": 14,
        "add_stats_id": 2,
        "type": RecordType.expense,
        "sort_order": 3,
    },
    {
        "name": "醫療",
        "icon_id": 20,
        "add_stats_id": 2,
        "type": RecordType.expense,
        "sort_order": 4,
    },
    {
        "name": "日用品",
        "icon_id": 16,
        "add_stats_id": 5,
        "type": RecordType.expense,
        "sort_order": 5,
    },
    {
        "name": "水電瓦斯",
        "icon_id": 95,
        "add_stats_id": 5,
        "type": RecordType.expense,
        "sort_order": 6,
    },
    {
        "name": "娛樂",
        "icon_id": 105,
        "add_stats_id": 4,
        "type": RecordType.expense,
        "sort_order": 7,
    },
    {
        "name": "社交",
        "icon_id": 50,
        "add_stats_id": 4,
        "type": RecordType.expense,
        "sort_order": 8,
    },
    {
        "name": "服飾",
        "icon_id": 35,
        "add_stats_id": 4,
        "type": RecordType.expense,
        "sort_order": 9,
    },
    {
        "name": "旅遊",
        "icon_id": 39,
        "add_stats_id": 4,
        "type": RecordType.expense,
        "sort_order": 10,
    },
    {
        "name": "寵物",
        "icon_id": 42,
        "add_stats_id": 3,
        "type": RecordType.expense,
        "sort_order": 11,
    },
    {
        "name": "3C",
        "icon_id": 27,
        "add_stats_id": 3,
        "type": RecordType.expense,
        "sort_order": 12,
    },
    {
        "name": "保險",
        "icon_id": 148,
        "add_stats_id": 3,
        "type": RecordType.expense,
        "sort_order": 13,
    },
    {
        "name": "薪資",
        "icon_id": 10,
        "add_stats_id": 6,
        "type": RecordType.income,
        "sort_order": 14,
    },
    {
        "name": "獎金",
        "icon_id": 11,
        "add_stats_id": 6,
        "type": RecordType.income,
        "sort_order": 15,
    },
    {
        "name": "投資",
        "icon_id": 13,
        "add_stats_id": 6,
        "type": RecordType.income,
        "sort_order": 16,
    },
]


def get_category_list(session: Session, user_id: int) -> list[CategoryList]:
    statement = (
        select(CategoryList, StatList.color)
        .join(StatList, CategoryList.add_stats_id == StatList.id, isouter=True)
        .where(CategoryList.user_id == user_id)
        .where(CategoryList.is_active == True)
        .order_by(CategoryList.sort_order.asc())
    )
    # result: 長得像 (CategoryList物件, color的值)-> 「tuple(元組)」
    results = session.exec(statement).all()
    # **(dict 展開)  .model_dump() 轉成 dict
    return [{**category.model_dump(), "color": color} for category, color in results]


def validate_category_by_user_id(
    session: Session, user_id: int, category_id: int
) -> None:
    statement = (
        select(CategoryList)
        .where(CategoryList.id == category_id)
        .where(CategoryList.user_id == user_id)
        .where(CategoryList.is_active == True)
    )
    result = session.exec(statement).first()

    if result is None:
        raise AppException(status_code=404, error_code="E02009", detail="建立失敗")


def create_default_categories(session: Session, user_id: int) -> None:
    # **category 把每個 dict 展開成關鍵字參數
    session.add_all(
        CategoryList(**category, user_id=user_id) for category in DEFAULT_CATEGORIES
    )


def insert_category(
    session: Session, user_id: int, data: CategoryCreate
) -> CategoryRead:
    max_order = session.exec(
        select(CategoryList.sort_order)
        .where(CategoryList.user_id == user_id)
        .where(CategoryList.type == data.type)
        .where(CategoryList.is_active == True)
        .order_by(CategoryList.sort_order.desc())
    ).first()

    new_sort_order = (max_order + 1) if max_order is not None else 0

    # ** dict type(有.keys() 的)
    # 物件 不等於 dict ->  data.model_dump() 把物件改成 dict
    category = CategoryList(
        **data.model_dump(), user_id=user_id, sort_order=new_sort_order
    )
    session.add(category)
    session.commit()
    session.refresh(category)

    return category


def update_category(
    session: Session, user_id: int, data: CategoryUpdate, category_id: int
) -> CategoryRead:
    if data.icon_id is not None:
        validate_icon_id(session, data.icon_id)

    if data.add_stats_id is not None:
        validate_stat_list(session, data.add_stats_id)

    category = session.get(CategoryList, category_id)

    if category is None or category.user_id != user_id or category.is_active == False:
        raise AppException(
            status_code=404, error_code="E01003", detail="找不到這筆紀錄"
        )

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)

    session.add(category)
    session.commit()
    session.refresh(category)
    return category


def update_category_order(session: Session, user_id: int, data: CategoryOrderUpdate):
    categories = session.exec(
        select(CategoryList)
        .where(CategoryList.user_id == user_id)
        .where(CategoryList.type == data.type)
        .where(CategoryList.is_active == True)
    ).all()

    _validate_category_ids_by_user(categories, data.category_ids)

    category_map = {category.id: category for category in categories}

    for index, category_id in enumerate(data.category_ids):
        category_map[category_id].sort_order = index

    session.commit()


def _validate_category_ids_by_user(
    categories: list[CategoryList],
    category_ids: list[int],
) -> None:
    # 使用 set 他會不管順序去比較兩個 set 裡面的東西有沒有一樣
    db_ids = {category.id for category in categories}
    submitted_ids = set(category_ids)
    if submitted_ids != db_ids:
        raise AppException(
            status_code=422, error_code="E01009", detail="有遺漏的 category"
        )


def remove_category(session: Session, user_id: int, category_id: int) -> None:
    category = session.get(CategoryList, category_id)

    if category is None or category.user_id != user_id:
        raise AppException(
            status_code=404, error_code="E01003", detail="找不到這筆紀錄"
        )

    category.is_active = False

    session.add(category)
    session.commit()
