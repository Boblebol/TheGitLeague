"""Celery tasks for automated award calculation."""

import logging
from datetime import datetime, timedelta

from app.core.celery_app import celery_app
from app.db.session import get_db_context
from app.services.award import award_service

logger = logging.getLogger(__name__)


@celery_app.task
def calculate_weekly_awards_task() -> dict:
    """
    Calculate Player of the Week awards.

    Scheduled to run every Monday at 00:00.
    Calculates awards for the previous week.

    Returns:
        Dictionary with task results
    """
    logger.info("Starting weekly awards calculation task")

    with get_db_context() as db:
        try:
            # Calculate last Monday
            today = datetime.now().date()
            days_since_monday = today.weekday()
            last_week_start = today - timedelta(days=days_since_monday + 7)

            awards_created = award_service.calculate_weekly_awards(db, last_week_start)

            logger.info(f"Weekly awards task completed: {awards_created} awards created")
            return {
                "success": True,
                "awards_created": awards_created,
                "week_start": last_week_start.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating weekly awards: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }


@celery_app.task
def calculate_monthly_awards_task() -> dict:
    """
    Calculate Player of the Month awards.

    Scheduled to run on the 1st of each month at 00:00.
    Calculates awards for the previous month.

    Returns:
        Dictionary with task results
    """
    logger.info("Starting monthly awards calculation task")

    with get_db_context() as db:
        try:
            # First day of last month
            today = datetime.now().date()
            if today.month == 1:
                last_month_start = today.replace(year=today.year - 1, month=12, day=1)
            else:
                last_month_start = today.replace(month=today.month - 1, day=1)

            awards_created = award_service.calculate_monthly_awards(db, last_month_start)

            logger.info(f"Monthly awards task completed: {awards_created} awards created")
            return {
                "success": True,
                "awards_created": awards_created,
                "month_start": last_month_start.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating monthly awards: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }


@celery_app.task
def calculate_rookie_of_month_task() -> dict:
    """
    Calculate Rookie of the Month awards.

    Scheduled to run on the 1st of each month at 00:00 (after monthly awards).
    Calculates rookie awards for the previous month.

    Returns:
        Dictionary with task results
    """
    logger.info("Starting Rookie of the Month calculation task")

    with get_db_context() as db:
        try:
            # First day of last month
            today = datetime.now().date()
            if today.month == 1:
                last_month_start = today.replace(year=today.year - 1, month=12, day=1)
            else:
                last_month_start = today.replace(month=today.month - 1, day=1)

            awards_created = award_service.calculate_rookie_of_month(db, last_month_start)

            logger.info(f"Rookie of Month task completed: {awards_created} awards created")
            return {
                "success": True,
                "awards_created": awards_created,
                "month_start": last_month_start.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating Rookie of Month: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }


@celery_app.task
def calculate_play_of_day_task() -> dict:
    """
    Calculate Play of the Day.

    Scheduled to run daily at 23:00.
    Selects the best commit from the current day.

    Returns:
        Dictionary with task results
    """
    logger.info("Starting Play of the Day calculation task")

    with get_db_context() as db:
        try:
            # Calculate for today (task runs at 23:00, so today's commits are available)
            target_date = datetime.now().date()

            plays_created = award_service.calculate_play_of_day(db, target_date)

            logger.info(f"Play of Day task completed: {plays_created} plays created")
            return {
                "success": True,
                "plays_created": plays_created,
                "date": target_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error calculating Play of Day: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
            }
