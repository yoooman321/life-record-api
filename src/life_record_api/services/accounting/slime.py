from sqlmodel import Session
from datetime import datetime, timezone
from life_record_api.exceptions import AppException

import random
from life_record_api.models.accounting import (
    Slimes,
    ProfessionType,
    Periods,
    PeriodStatus,
)
from life_record_api.schemas.accounting import SlimeEdit

from life_record_api.services.accounting.stat_calculation import (
    calculate_stat,
    get_periods_days,
)

profession_mapping = {
    "str": ProfessionType.warrior,
    "int": ProfessionType.wizard,
    "luk": ProfessionType.thief,
    "power": ProfessionType.paladin,
    "dex": ProfessionType.bowman,
}


name_mapping = {
    ProfessionType.warrior: "好戰史萊姆",
    ProfessionType.wizard: "魔力史萊姆",
    ProfessionType.thief: "都摟播史萊姆",
    ProfessionType.paladin: "神聖史萊姆",
    ProfessionType.bowman: "史萊姆箭士",
}


def insert_slime(session: Session, period: Periods, user_id: int) -> Slimes | None:
    period.status = PeriodStatus.completed
    period.actual_end_at = datetime.now(timezone.utc)

    days = get_periods_days(period)

    stats = calculate_stat(session, period.id, user_id, days)
    stats_without_cash = {key: value for key, value in stats.items() if key != "cash"}
    max_value = max(stats_without_cash.values())
    tied_stats = [
        key for key, value in stats_without_cash.items() if value == max_value
    ]
    max_stat = random.choice(tied_stats)
    profession = profession_mapping[max_stat]

    slime = Slimes(
        period_id=period.id,
        user_id=user_id,
        power=stats["str"],
        agility=stats["dex"],
        luck=stats["luk"],
        intelligence=stats["int"],
        stamina=stats["power"],
        wealth=stats["cash"],
        profession=profession,
        name=name_mapping[profession],
    )

    session.add(slime)
    session.flush()

    session.add(period)
    session.commit()

    session.refresh(slime)

    return slime


def update_slime(session: Session, data: SlimeEdit) -> Slimes:
    slime = session.get(Slimes, data.id)
    if slime is None:
        raise AppException(
            status_code=404, error_code="E01007", detail="找不到這隻史萊姆"
        )
    slime.name = data.name
    session.add(slime)
    session.commit()
    session.refresh(slime)
    return slime
