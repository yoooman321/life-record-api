from sqlmodel import Session, select
from life_record_api.models.accounting import StatList, CalcMethod
from life_record_api.exceptions import (
    AppException,
)

STAT_MAX_VALUE_PER_DAY = 3


def get_stat_info(session: Session, days: int) -> dict[int, dict]:
    statement = select(StatList)
    results = session.exec(statement).all()

    return {
        stat.id: {
            "name": stat.name,
            "method": stat.calc_method,
            "max": STAT_MAX_VALUE_PER_DAY * days,
        }
        for stat in results
    }


def get_stat_list(session: Session) -> list[StatList]:
    statement = select(StatList)
    results = session.exec(statement).all()
    return results


def validate_stat_list(session: Session, stats_id: int) -> None:
    stats = session.exec(select(StatList).where(StatList.id == stats_id)).first()

    if stats is None:
        raise AppException(
            status_code=404, error_code="E01003", detail="找不到這筆紀錄"
        )
