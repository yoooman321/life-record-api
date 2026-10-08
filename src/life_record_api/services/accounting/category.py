from sqlmodel import Session, select
from life_record_api.models.accounting import RecordType

from life_record_api.models.accounting import CategoryList, StatList
from life_record_api.exceptions import (
    AppException,
)


DEFAULT_CATEGORIES = [
    {"name": "食物", "icon_id": 1, "add_stats_id": 1, "type": RecordType.expense},
    {"name": "點心", "icon_id": 139, "add_stats_id": 1, "type": RecordType.expense},
    {"name": "飲料", "icon_id": 7, "add_stats_id": 1, "type": RecordType.expense},
    {"name": "交通", "icon_id": 14, "add_stats_id": 2, "type": RecordType.expense},
    {"name": "醫療", "icon_id": 20, "add_stats_id": 2, "type": RecordType.expense},
    {"name": "日用品", "icon_id": 16, "add_stats_id": 5, "type": RecordType.expense},
    {"name": "水電瓦斯", "icon_id": 95, "add_stats_id": 5, "type": RecordType.expense},
    {"name": "娛樂", "icon_id": 105, "add_stats_id": 4, "type": RecordType.expense},
    {"name": "社交", "icon_id": 50, "add_stats_id": 4, "type": RecordType.expense},
    {"name": "服飾", "icon_id": 35, "add_stats_id": 4, "type": RecordType.expense},
    {"name": "旅遊", "icon_id": 39, "add_stats_id": 4, "type": RecordType.expense},
    {"name": "寵物", "icon_id": 42, "add_stats_id": 3, "type": RecordType.expense},
    {"name": "3C", "icon_id": 27, "add_stats_id": 3, "type": RecordType.expense},
    {"name": "保險", "icon_id": 148, "add_stats_id": 3, "type": RecordType.expense},
    {"name": "薪資", "icon_id": 10, "add_stats_id": 6, "type": RecordType.income},
    {"name": "獎金", "icon_id": 11, "add_stats_id": 6, "type": RecordType.income},
    {"name": "投資", "icon_id": 13, "add_stats_id": 6, "type": RecordType.income},
]


def get_category_list(session: Session, user_id: int) -> list[CategoryList]:
    statement = (
        select(CategoryList, StatList.color)
        .join(StatList, CategoryList.add_stats_id == StatList.id, isouter=True)
        .where(CategoryList.user_id == user_id)
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
    )
    result = session.exec(statement).first()

    if result is None:
        raise AppException(status_code=404, error_code="E02009", detail="建立失敗")


def create_default_categories(session: Session, user_id: int) -> None:
    # **category 把每個 dict 展開成關鍵字參數
    session.add_all(
        CategoryList(**category, user_id=user_id) for category in DEFAULT_CATEGORIES
    )
