from sqlmodel import Session, select
from life_record_api.models.accounting import StatList, CalcMethod

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
