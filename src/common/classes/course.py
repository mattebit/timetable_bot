from src.common.classes.lecture import Lecture
from src.common.methods.utils import University


class Course:
    name : str
    id : str # some type of unique identifier wrt to other courses
    professor_name : str
    lectures : list[Lecture]
    university: University

    def __init__(self):
        self.name = ""
        self.id = ""
        self.professor_name = ""
        self.lectures = []
        self.university = -1