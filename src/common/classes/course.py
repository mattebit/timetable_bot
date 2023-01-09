import src.common.classes.lecture as lecture
import src.common.methods.unitn_activities as unitn_activities
import src.common.methods.utils as utils


class Course:
    name: str
    id: str  # some type of unique identifier wrt to other courses
    professor_name: str
    lectures: list[lecture.Lecture]
    university: utils.University

    def __init__(self):
        self.name = ""
        self.id = ""
        self.professor_name = ""
        self.lectures = []
        self.university = -1
        self.cancelled = False

    def fetch_lectures(self) -> list[lecture.Lecture]:
        """
        Fetch all the lectures of this course, the variable university needs to be set correctly.

        Returns:
            object: also returns the list of lectures for convenience
        Raises:
            Exception: if an university is not specified
        """
        if self.university == utils.University.UNITN:
            self.lectures = unitn_activities.list_lezione_to_list_lecture(
                unitn_activities.fetch_lectures(self.id, True))
            pass
        elif self.university == utils.University.UNIBZ:
            pass
        else:
            raise Exception("University not specified")

        return self.lectures


def group_courses_by_uni(courses: list[Course]) -> dict[utils.University, list[Course]]:
    res: dict[utils.University, list[Course]] = {}
    for c in courses:
        if not c.university in res.keys():
            res[c.university] = []
        res[c.university].append(c)

    return res
