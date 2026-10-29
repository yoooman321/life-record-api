from sqlmodel import Session, select

from life_record_api.models.accounting import IconList
from life_record_api.exceptions import (
    AppException,
)


def get_icon_list(session: Session) -> list[IconList]:
    # SELECT * FROM icon_list
    statement = select(IconList)
    return session.exec(statement).all()


def validate_icon_id(session: Session, icon_id: int) -> None:
    icon = session.exec(select(IconList).where(IconList.id == icon_id)).first()
    if icon is None:
        raise AppException(
            status_code=404, error_code="E01003", detail="找不到這筆紀錄"
        )
