from sqlmodel import Session, select

from life_record_api.models.accounting import TagList
from life_record_api.schemas.accounting import TagCreate


def get_tag_list(session: Session, user_id: int) -> list[TagList]:
    statement = select(TagList).where(TagList.user_id == user_id)
    return session.exec(statement).all()


def insert_tag(session: Session, data: TagCreate, user_id: int) -> TagList:
    tag = TagList(**data.model_dump(), user_id=user_id)
    session.add(tag)
    session.commit()
    session.refresh(tag)

    return tag
