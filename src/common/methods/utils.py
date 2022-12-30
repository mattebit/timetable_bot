import re
from datetime import datetime
from enum import Enum

from src.common.classes.course import Course
from src.common.classes.user import Userinfo
from src.common.methods.google import addEvent, getService


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

    timestamp_start = datetime.fromtimestamp(date_timestamp).replace(hour=start_hour, minute=start_minutes)
    timestamp_end = datetime.fromtimestamp(date_timestamp).replace(hour=end_hour, minute=end_minutes)

    return timestamp_start, timestamp_end


def update_lectures_to_calendar(userinfo: Userinfo):
    service = getService(userinfo.credentials)
    #TODO: Fetch all events and remove the not used one

    for c in userinfo.follwoing_courses:
        for lec in c.lectures:
            if len(lec.calendar_event_id) == 0:
                # TODO: Check if id of event is updated
                addEvent(service,
                     userinfo.calendar_id,
                     lec)
            else:
                pass
                # TODO: validate the local calendar to the remote one
                # TODO: getEvent()
                # TODO: validate()

def group_courses_by_uni(courses: list[Course]) -> dict[University, list[Course]]:
    res : dict[University, list[Course]] = {}
    for c in courses:
        res[c.university].append(c)

    return res