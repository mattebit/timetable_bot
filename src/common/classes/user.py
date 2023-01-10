import src.common.classes.course as course
import src.common.classes.lecture as lecture


class Userinfo:
    """
    Class containing information about a bot user. It also stores the list of courses he is following, the
    token to SSO into google calendar and the google calendar id
    """
    follwoing_courses: list[course.Course]
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

    def get_all_lectures(self) -> list[lecture.Lecture]:
        """
        Get all the lectures the user is following
        Returns: a list containing all the lectures the user is following
        """
        res: list[lecture.Lecture] = []
        for c in self.follwoing_courses:
            res.extend(c.lectures)

        return res
