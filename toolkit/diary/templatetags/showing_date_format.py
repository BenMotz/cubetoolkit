"""
Filter to format a list of showings as a human readable date range
"""

import datetime

from django import template
from django.utils.timezone import get_current_timezone

register = template.Library()


def _ordinal_suffix(i):
    if i < 4 or i > 30 or 20 < i < 24:
        return [None, "st", "nd", "rd"][i % 10]
    else:
        return "th"


def _output_month(year, month, day_list, d_time):
    # Passed a list of days in a given month/year. Formats as one of:
    # 0 length day_list: ''
    # 1 length day_list: 'Wed 1st'
    # 2 length sequential day_list: 'Wed 1st / Thu 2nd'
    # 3+ length sequential day_list: 'Wed 1st - Fri 3rd'
    # 4+ length non-sequential day_list: 'Wed 1st / Fri 3rd - Sun 5th'
    # ...plus appends the time given in d_time

    prev = -99
    seq_len = 0

    op = []

    def _format_day(day):
        date = datetime.datetime(year=year, month=month, day=day)
        return date.strftime("%a %-d%%s") % (_ordinal_suffix(day))

    for d in day_list:
        if seq_len == 0:
            # Always output the first date in the month:
            op.append(_format_day(d))
            prev = d
            seq_len = 1
        elif d == prev + 1:
            # Don't output if the date follows sequentially, but count how
            # many sequential dates there've been
            seq_len += 1
            prev = d
        else:
            # Current doesn't follow sequentially: output the (previously
            # seen) end of the sequence
            if seq_len == 1:
                # Only two items in the sequence: output a list
                op.append(f", {_format_day(d)}")
            elif seq_len == 2:
                # Only two items in the sequence: output a list
                op.append(f", {_format_day(prev)}, {_format_day(d)}")
            else:
                # > 2 items in the sequence, output a range
                op.append(f"\u2013{_format_day(prev)}, {_format_day(d)}")
            # (In both cases, also output the start of the next sequence)
            seq_len = 1
            prev = d

    # Finish off: if seq_len == 1 then no output is needed
    if seq_len == 2:
        op.append(f", {_format_day(prev)}")
    elif seq_len > 2:
        op.append(f"\u2013{_format_day(prev)}")

    # Print the start time. Only show the minutes when the start isn't on the
    # hour:
    if d_time.minute == 0:
        time_string = d_time.strftime("%-I%p")
    else:
        time_string = d_time.strftime("%-I:%M%p")

    return "{} / {}".format("".join(op), time_string.lower())


def _pretty_print_dateset(dates):
    if not dates:
        return ""

    current_tz = get_current_timezone()
    out_strings = []
    month = dates[0].month
    year = dates[0].year
    time = dates[0].astimezone(current_tz).time()
    day_list = []
    # Assume the dates are sorted. Group by month, and pass list of days of
    # month into _output_month
    for dt in dates:
        dt_time = dt.astimezone(current_tz).time()
        if dt.month != month or dt_time != time:
            out_strings.append(_output_month(year, month, day_list, time))
            time = dt_time
            month = dt.month
            year = dt.year
            day_list = [dt.day]
        else:
            day_list.append(dt.day)

    out_strings.append(_output_month(year, month, day_list, time))

    return ", ".join(out_strings)


@register.filter(name="showingdates")
def format_showing_dates(showings):
    dates = [s.start for s in showings]
    return _pretty_print_dateset(dates)
