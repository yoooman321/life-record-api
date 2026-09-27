from sqlmodel import Session, select

from life_record_api.models.accounting import CategoryList, StatList


def get_category_list(session: Session, user_id: int = 0) -> list[CategoryList]:
    statement = (
        select(CategoryList, StatList.color)
        .join(StatList, CategoryList.add_stats_id == StatList.id, isouter=True)
        .where(CategoryList.user_id == user_id)
    )
    # result: 長得像 (CategoryList物件, color的值)-> 「tuple(元組)」
    results = session.exec(statement).all()
    # **(dict 展開)  .model_dump() 轉成 dict
    return [{**category.model_dump(), "color": color} for category, color in results]

