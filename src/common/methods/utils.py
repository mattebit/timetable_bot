import re
from datetime import datetime, timezone, timedelta
from enum import Enum


class University(Enum):
    UNITN = 0
    UNIBZ = 1


def parseHourString(hour_string: str) -> tuple[int | None, int | None, int | None]:
    pattern = "(\d?\d):(\d?\d):?(\d?\d)?"
    r = re.match(pattern, hour_string)
    hours = r.group(1)
    minutes = r.group(2)
    seconds = r.group(3)
    if not hours is None:
        hours = int(hours)
    if not minutes is None:
        minutes = int(minutes)
    if not seconds is None:
        seconds = int(seconds)

    return hours, minutes, seconds


def get_lecture_start_end_timestamps(ora_inizio: str,
                                     ora_fine: str,
                                     date_timestamp: int) -> tuple[datetime, datetime]:
    start_hour, start_minutes, _ = parseHourString(ora_inizio)
    end_hour, end_minutes, _ = parseHourString(ora_fine)

    timestamp_start = datetime.fromtimestamp(date_timestamp).replace(hour=start_hour, minute=start_minutes, tzinfo=None)
    timestamp_end = datetime.fromtimestamp(date_timestamp).replace(hour=end_hour, minute=end_minutes, tzinfo=None)

    return timestamp_start, timestamp_end

"""
def ics_calendar_to_csv(ics_calendar : Calendar()) -> str:
    # TODO: If have time
    convert = Convert()
    convert.cal = ics_calendar
    convert.make_csv()
    convert.save_csv("prova.csv")
"""