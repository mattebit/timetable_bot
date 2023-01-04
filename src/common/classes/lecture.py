from ics import Event

class Lecture:
    event : Event
    calendar_event_id : str

    def __init__(self):
        self.event = None
        self.calendar_event_id = ""