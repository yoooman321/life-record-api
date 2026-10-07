from sqlmodel import Session, select
from life_record_api.exceptions import AppException
from life_record_api.schemas.accounting import PeriodsCreate
from life_record_api.models.accounting import DurationType, Periods, PeriodStatus
from datetime import datetime, time, timedelta, timezone

DURATION_MAP: dict[DurationType, timedelta] = {
    DurationType.oneday: timedelta(days=1),
    DurationType.twoday: timedelta(days=2),
    DurationType.week: timedelta(weeks=1),
    DurationType.month: timedelta(days=30),
}


def _calculate_planned_end_at(data: PeriodsCreate, started_at: datetime) -> datetime:
    if data.duration_type == DurationType.custom:
        duration = timedelta(days=data.days)
    else:
        duration = DURATION_MAP[data.duration_type]

    end_date = (started_at + duration).date()
    return datetime.combine(end_date, time(23, 59, 59), tzinfo=timezone.utc)


def _validate_duration(data: PeriodsCreate) -> None:
    if data.duration_type == DurationType.custom and data.days is None:
        raise AppException(status_code=422, error_code="E01005", detail="時間少了日期")


def get_growing_period(session: Session, user_id: int) -> Periods | None:
    statement = (
        select(Periods)
        .where(Periods.user_id == user_id)
        .where(Periods.status == PeriodStatus.growing)
    )
    period = session.exec(statement).first()

    return period


def is_period_expired(period: Periods) -> bool:
    return (
        period.actual_end_at is None
        and datetime.now(timezone.utc) >= period.planned_end_at
    )


def _validate_growing_status_exist(session: Session, user_id: int) -> None:
    period = get_growing_period(session, user_id)
    if period is not None:
        raise AppException(
            status_code=409, error_code="E01006", detail="已有存在的史萊姆"
        )


def insert_period(session: Session, data: PeriodsCreate, user_id: int) -> Periods:
    _validate_duration(data)
    _validate_growing_status_exist(session, user_id)

    started_at = datetime.now(timezone.utc)
    planned_end_at = _calculate_planned_end_at(data, started_at)

    period = Periods(
        user_id=user_id,
        duration_type=data.duration_type,
        started_at=started_at,
        planned_end_at=planned_end_at,
        status=PeriodStatus.growing,
    )

    session.add(period)
    session.commit()
    session.refresh(period)
    return period
