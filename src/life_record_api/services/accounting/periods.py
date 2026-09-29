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


def _complete_if_expired(session: Session, period: Periods) -> Periods:
    now = datetime.now(timezone.utc)
    if now >= period.planned_end_at:
        period.actual_end_at = period.planned_end_at
        period.status = PeriodStatus.completed
        session.add(period)
        session.commit()
        session.refresh(period)
    return period


def get_growing_period_id(session: Session, user_id: int = 0) -> int | None:
    statement = (
        select(Periods)
        .where(Periods.user_id == user_id)
        .where(Periods.status == PeriodStatus.growing)
    )
    period = session.exec(statement).first()

    if period is None:
        return None

    period = _complete_if_expired(session, period)

    if period.status != PeriodStatus.growing:
        return None

    return period.id


def _validate_growing_status_exist(session: Session, user_id: int = 0) -> None:
    period_id = get_growing_period_id(session, user_id)
    if period_id is not None:
        raise AppException(
            status_code=409, error_code="E01006", detail="已有存在的史萊姆"
        )


def insert_period(session: Session, data: PeriodsCreate, user_id: int = 0) -> Periods:
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


def end_growing_period(session: Session, user_id: int = 0) -> Periods:
    period_id = get_growing_period_id(session, user_id)

    if period_id is None:
        raise AppException(
            status_code=404, error_code="E01002", detail="目前沒有正在培育的史萊姆"
        )
    period = session.get(Periods, period_id)
    period.actual_end_at = datetime.now(timezone.utc)
    period.status = PeriodStatus.completed

    session.add(period)
    session.commit()
    session.refresh(period)
    return period


def get_period_days(session: Session, period_id: int):
    statement = select(Periods).where(Periods.id == period_id)
    period = session.exec(statement).first()
    end_at = (
        period.actual_end_at
        if period.actual_end_at is not None
        else period.planned_end_at
    )
    return {
        "started_at": period.started_at,
        "ended_at": end_at,
        "days": (end_at - period.started_at).days,
    }
