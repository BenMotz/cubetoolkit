"""Code shared between both public and editing sets of diary views"""
import calendar
import logging
import datetime

logger = logging.getLogger(__name__)


def get_date_range(year, month, day, user_days_ahead):
    """Support method to take fields read from HTTP request and return a tuple
    (datetime, number_of_days)
    If month or day are blank, they default to 1. If all three are blank it
    defaults to today.
    If there is an error in the parameters, returns (None, "Error mesage)"""
    if day is not None and month is None:
        logger.error("Invalid request; can't specify day and no month")
        return (None, "Invalid request; can't specify day and no month")

    try:
        year = int(year) if year else None
        month = int(month) if month else None
        day = int(day) if day else None
    except ValueError:
        logger.error("Invalid value requested in date range, one of day {0}, month {1}, year {2}"
                     .format(day, month, year))
        return (None, "Invalid values")

    logger.debug("Range: day %s, month %s, year %s, span %s days",
                 str(day), str(month), str(year), str(user_days_ahead))

    try:
        if day:
            startdate = datetime.date(year, month, day)
            days_ahead = 1
        elif month:
            startdate = datetime.date(year, month, 1)
            days_ahead = calendar.monthrange(year, month)[1]
        elif year:
            startdate = datetime.date(year, 1, 1)
            days_ahead = 365
            if calendar.isleap(year):
                days_ahead += 1
        else:
            startdate = datetime.date.today()
            days_ahead = 30  # default
    except ValueError as vale:
        logger.error("Invalid something requested in date range: {0}".format(vale))
        return (None, "Invalid date")

    if user_days_ahead:
        try:
            days_ahead = int(user_days_ahead)
        except (ValueError, TypeError):
            pass

    return startdate, days_ahead
