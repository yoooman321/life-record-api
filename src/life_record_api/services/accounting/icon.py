from sqlmodel import Session, select

from life_record_api.models.accounting import IconList


def get_icon_list(session: Session) -> list[IconList]:
    # SELECT * FROM icon_list
    statement = select(IconList)
    return session.exec(statement).all()
