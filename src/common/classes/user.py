import src.common.classes.course as course


class Userinfo:
    follwoing_courses : list[course.Course]
    calendar_id: str
    has_calendar: bool
    consent_given: bool
    credentials: any
    flow: any

    def __init__(self):
        self.follwoing_courses = []
        self.calendar_id = None
        self.has_calendar = False
        self.consent_given = False
        self.credentials = None
        self.flow = None
