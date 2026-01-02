"""Period derivation utilities."""

from datetime import datetime, date, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.models.season import Season


def get_period_start(dt: datetime, period_type: str, season: Optional[Season] = None) -> date:
    """
    Get the start date of the period containing 'dt'.

    Examples:
      dt = 2024-01-17 (Wednesday)
      period_type = 'week' → 2024-01-15 (Monday)
      period_type = 'month' → 2024-01-01
      period_type = 'day' → 2024-01-17

    Args:
        dt: Datetime to find period for
        period_type: Type of period ('day', 'week', 'month', 'season')
        season: Season object (required for 'season' period_type)

    Returns:
        Start date of the period

    Raises:
        ValueError: If period_type is invalid or season is missing for 'season' period_type
    """
    if period_type == 'day':
        return dt.date()
    elif period_type == 'week':
        # Monday of the week (weekday() returns 0 for Monday)
        return (dt - timedelta(days=dt.weekday())).date()
    elif period_type == 'month':
        return dt.replace(day=1).date()
    elif period_type == 'season':
        if not season:
            raise ValueError("Season object required for 'season' period_type")
        return season.start_at.date()
    else:
        raise ValueError(f"Invalid period_type: {period_type}. Must be one of: day, week, month, season")


def get_period_end(dt: datetime, period_type: str, season: Optional[Season] = None) -> date:
    """
    Get the end date of the period containing 'dt'.

    Args:
        dt: Datetime to find period for
        period_type: Type of period ('day', 'week', 'month', 'season')
        season: Season object (required for 'season' period_type)

    Returns:
        End date of the period

    Raises:
        ValueError: If period_type is invalid or season is missing for 'season' period_type
    """
    if period_type == 'day':
        return dt.date()
    elif period_type == 'week':
        # Sunday of the week
        start = get_period_start(dt, 'week')
        return start + timedelta(days=6)
    elif period_type == 'month':
        # Last day of the month
        if dt.month == 12:
            next_month = dt.replace(year=dt.year + 1, month=1, day=1)
        else:
            next_month = dt.replace(month=dt.month + 1, day=1)
        return (next_month - timedelta(days=1)).date()
    elif period_type == 'season':
        if not season:
            raise ValueError("Season object required for 'season' period_type")
        return season.end_at.date()
    else:
        raise ValueError(f"Invalid period_type: {period_type}")


def get_period_range(dt: datetime, period_type: str, season: Optional[Season] = None) -> Tuple[date, date]:
    """
    Get the start and end dates of the period containing 'dt'.

    Args:
        dt: Datetime to find period for
        period_type: Type of period ('day', 'week', 'month', 'season')
        season: Season object (required for 'season' period_type)

    Returns:
        Tuple of (start_date, end_date)
    """
    start = get_period_start(dt, period_type, season)
    end = get_period_end(dt, period_type, season)
    return start, end


def get_season_for_date(dt: datetime, project_id: str, db: Session) -> Optional[Season]:
    """
    Find the season that contains a given date for a project.

    Args:
        dt: Datetime to find season for
        project_id: Project ID
        db: Database session

    Returns:
        Season object or None if no season contains this date
    """
    return (
        db.query(Season)
        .filter(
            Season.project_id == project_id,
            Season.start_at <= dt,
            Season.end_at >= dt,
        )
        .first()
    )


def get_active_season(project_id: str, db: Session) -> Optional[Season]:
    """
    Get the active season for a project.

    Args:
        project_id: Project ID
        db: Database session

    Returns:
        Active Season object or None
    """
    from app.models.season import SeasonStatus
    
    return (
        db.query(Season)
        .filter(
            Season.project_id == project_id,
            Season.status == SeasonStatus.ACTIVE,
        )
        .first()
    )


def is_date_in_period(
    dt: date,
    period_start: date,
    period_type: str,
    season: Optional[Season] = None
) -> bool:
    """
    Check if a date falls within a specific period.

    Args:
        dt: Date to check
        period_start: Start date of the period
        period_type: Type of period
        season: Season object (required for 'season' period_type)

    Returns:
        True if date is in period, False otherwise
    """
    # Get the period range
    start, end = get_period_range(
        datetime.combine(period_start, datetime.min.time()),
        period_type,
        season
    )
    
    return start <= dt <= end
