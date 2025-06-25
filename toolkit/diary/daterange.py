"""Code shared between both public and editing sets of diary views"""

from typing import Optional, Tuple, Union
import calendar
import logging
from datetime import datetime
import django.utils.timezone

logger = logging.getLogger(__name__)


def get_date_range(
    year: Optional[int],
    month: Optional[int],
    day: Optional[int],
    user_days_ahead: Optional[int],
    default_days_ahead: int = 365,
) -> Union[Tuple[datetime, int], Tuple[None, str]]:
    """Support method to take fields read from HTTP request and return a tuple
    (datetime, number_of_days)
    If month or day are blank, they default to 1. If all three are blank it
    defaults to today. The datetime will be localised to the current timezone.
    If there is an error in the parameters, returns (None, "Error mesage)"""
    if day is not None and month is None:
        logger.error("Invalid request; can't specify day and no month")
        return (None, "Invalid request; can't specify day and no month")

    try:
        year = int(year) if year else None
        month = int(month) if month else None
        day = int(day) if day else None
    except ValueError:
        logger.error(
            "Invalid value requested in date range, one of day {0}, "
            "month {1}, year {2}".format(day, month, year)
        )
        return (None, "Invalid values")

    if year and (year > 2100 or year < 1990):
        return (None, "Invalid values")

    current_tz = django.utils.timezone.get_current_timezone()

    try:
        if year and month and day:
            startdate = datetime(year, month, day, tzinfo=current_tz)
            days_ahead = 1
        elif year and month:
            startdate = datetime(year, month, 1, tzinfo=current_tz)
            days_ahead = calendar.monthrange(year, month)[1]
        elif year:
            startdate = datetime(year, 1, 1, tzinfo=current_tz)
            days_ahead = 365
            if calendar.isleap(year):
                days_ahead += 1
        else:
            # Fiddly way to set startdate to the start of the local day:
            # Get current UTC time and convert to local time:
            now_local = django.utils.timezone.localtime(
                django.utils.timezone.now()
            )
            # Create a new local time with hour/min/sec set to zero:
            startdate = datetime(
                now_local.year,
                now_local.month,
                now_local.day,
                tzinfo=current_tz,
            )

            days_ahead = int(default_days_ahead)
    except (OverflowError, ValueError) as vale:
        logger.error(f"Invalid something requested in date range: {vale}")
        return (None, "Invalid date")

    if user_days_ahead:
        try:
            days_ahead = int(user_days_ahead)
            days_ahead = 0 if days_ahead < 0 else days_ahead
            # Three years should be enough for anyone, right?
            days_ahead = 1095 if days_ahead > 1095 else days_ahead
        except (ValueError, TypeError):
            pass

    return startdate, days_ahead
