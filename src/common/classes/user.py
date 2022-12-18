from common.classes.unitn import Attivita, Lezione


class Userinfo:
    following_activities: list[Attivita]
    following_lectures: list[Lezione]
    calendar_id: str
    has_calendar: bool
    consent_given: bool
    credentials: any
    flow: any

    def __init__(self):
        self.following_lectures = []
        self.following_lectures = []
        self.calendar_id = None
        self.has_calendar = False
        self.consent_given = False
        self.credentials = None
        self.flow = None
