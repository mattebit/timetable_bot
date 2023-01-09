import copy

from ics import Event


class Lecture:
    event: Event
    calendar_event_id: str

    def __init__(self):
        self.event = Event()
        self.event.status = "CONFIRMED"
        self.calendar_event_id = ""

    def __eq__(self, other):
        is_equal = self.event == other.event
        if is_equal:
            if self.calendar_event_id != "":
                other.calendar_event_id = self.calendar_event_id
            elif other.calendar_event_id != "":
                self.calendar_event_id = other.calendar_event_id

        return is_equal


def diff(local: list[Lecture], remote: list[Lecture]):
    equal = []
    edited_local = copy.deepcopy(local)
    edited_remote = copy.deepcopy(remote)

    calendar_to_add: list[Lecture] = []
    local_to_update: list[Lecture] = []
    calendar_to_remove: list[Lecture] = []

    for i in local:
        if i.calendar_event_id == "":
            calendar_to_add.append(i)
            edited_local.remove(i)

    tmp_local = copy.deepcopy(edited_local)  # do not remove, it is needed
    tmp_remote = copy.deepcopy(edited_remote)  # do not remove, it is needed

    for i in tmp_local:
        for j in tmp_remote:
            if i == j:
                equal.append(i)
                edited_local.remove(i)
                edited_remote.remove(j)

    tmp_local = copy.deepcopy(edited_local)  # do not remove, it is needed
    tmp_remote = copy.deepcopy(edited_remote)  # do not remove, it is needed

    for i in tmp_local:
        for j in tmp_remote:
            if i.calendar_event_id == j.calendar_event_id:
                local_to_update.append(j)
                edited_local.remove(i)
                edited_remote.remove(j)

    tmp_remote = copy.deepcopy(edited_remote)  # do not remove, it is needed

    for j in tmp_remote:
        calendar_to_remove.append(j)

    return calendar_to_add, local_to_update, calendar_to_remove
