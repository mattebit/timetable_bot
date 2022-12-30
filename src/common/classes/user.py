from src.common.classes.course import Course

class Userinfo:
    follwoing_courses : list[Course]
    calendar_id: str
    has_calendar: bool
    consent_given: bool
    credentials: any
    flow: any

    def __init__(self):
        self.follwoing_courses = []
        self.following_activities = {}
        self.following_lectures = {}
        self.calendar_id = None
        self.has_calendar = False
        self.consent_given = False
        self.credentials = None
        self.flow = None
