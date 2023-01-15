import common.classes.lecture as lecture
import common.methods.utils as utils


class Course:
    """
    This class stores a university course, and the related lectures
    """
    name: str
    id: str  # some type of unique identifier wrt to other courses
    professor_name: str
    lectures: list[lecture.Lecture]
    university: utils.University

    def __init__(self):
        """
        Initialize a Course object
        """
        self.name = ""
        self.id = ""
        self.professor_name = ""
        self.lectures = []
        self.university = -1
        self.cancelled = False


def group_courses_by_uni(courses: list[Course]) -> dict[utils.University, list[Course]]:
    """
    Given a list of courses, group them by university.
    Args:
        courses: the list of courses

    Returns: a dictionary, having univerisies as keys, and a list of courses as value
    """
    res: dict[utils.University, list[Course]] = {}
    for c in courses:
        if not c.university in res.keys():
            res[c.university] = []
        res[c.university].append(c)

    return res


def group_lectures_in_courses(lectures: list[lecture.Lecture], uni: utils.University) -> list[Course]:
    res : list[Course] = []
    batch : dict[str, list[lecture.Lecture]] = {}

    for lec in lectures:
        if not lec.event.name in batch.keys():
            batch[lec.event.name] = []
        batch[lec.event.name].append(lec)

    for name in batch.keys():
        c = Course()
        c.name = name
        c.university = uni
        c.lectures = batch[name]
        c.professor_name = batch[name][0].event.description

        res.append(c)

    return res