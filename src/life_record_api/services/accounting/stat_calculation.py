from sqlmodel import Session, select
from life_record_api.models.accounting import (
    AccountingRecords,
    CategoryList,
    CalcMethod,
    Periods,
)
from life_record_api.services.accounting.stat_list import get_stat_info


def _get_records_with_stats(session: Session, period_id: int, user_id) -> list[dict]:
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


def calculate_stat(session: Session, period_id: int, user_id, days: int):
    records = _get_records_with_stats(session, period_id, user_id)
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


def get_actual_end_date(period: Periods):
    end_at = (
        period.actual_end_at
        if period.actual_end_at is not None
        else period.planned_end_at
    )
    return end_at


def get_periods_days(period: Periods) -> int:
    end_at = get_actual_end_date(period)
    return max(1, (end_at - period.started_at).days)
