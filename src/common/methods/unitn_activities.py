import datetime
import json
from typing import cast

import requests
from ics import Event

import src.common.classes.course as course
# Avoid from ... import * because of circular imports problems
# https://stackoverflow.com/questions/5748946/pythonic-way-to-resolve-circular-import-statements
import src.common.classes.lecture as lecture
import src.common.classes.unitn as unitn
import src.common.methods.utils as utils

UNITN_COMBO_ENDPOINT = "https://easyacademy.unitn.it/AgendaStudentiUnitn/combo.php"
UNITN_GRID_ENDPOINT = "https://easyacademy.unitn.it/AgendaStudentiUnitn/grid_call.php"


def filter_activities(activities: list[unitn.Attivita], filter_by: str) -> list[unitn.Attivita]:
    res = []
    for act in activities:
        if filter_by in act['nome_insegnamento']:
            res.append(act)
    return res


def fetch_activities() -> list[unitn.Attivita]:
    year = 2022  # str(datetime.date.today().year)
    # TODO: urllib urlparse purify
    url = UNITN_COMBO_ENDPOINT + f"?sw=ec_&aa={year}&page=attivita"

    resp = requests.request(
        method="GET",
        url=url
    )

    # clean output
    resp = resp.text.split('var elenco_attivita = ')[1]  # has js inside
    resp = resp[0:len(resp) - 3]  # has a trailing ";"

    l = json.loads(resp)
    activity_list = []

    for i in l:
        activity_list.append(cast(unitn.Attivita, i))

    return activity_list


# the date filters the week activities
def fetch_lectures(attivita_id: str, all_events: bool = False) -> list[unitn.Lezione]:
    year = 2022  # str(datetime.date.today().year)
    date = datetime.date.today().strftime('%d-%m-%Y')  # italian format
    if all_events:
        all_events = 1
    else:
        all_events = 0

    # TODO: urllib urlparse purify
    query = f"?view=easycourse&form-type=attivita&include=attivita&anno={year}&attivita%5B%5D={attivita_id}&" \
            f"visualizzazione_orario=cal&date={date}&list=&week_grid_type=-1&col_cells=0&empty_box=0&" \
            f"only_grid=0&highlighted_date=0&faculty_group=0&_lang=en&all_events={all_events}"

    url = UNITN_GRID_ENDPOINT + query

    resp = requests.request(
        method="GET",
        url=url
    )

    j: unitn.GridCallResponse = resp.json()

    lecture_list: list[unitn.Lezione] = []
    lecture_list = j['celle']

    # Create start and end unix timestampss
    for l in lecture_list:
        start_timestamp, end_timestamp = utils.get_lecture_start_end_timestamps(
            l['ora_inizio'], l['ora_fine'], l['timestamp'])
        l['timestamp_start'] = start_timestamp
        l['timestamp_end'] = end_timestamp
        l['calendar_event_id'] = ""

    return lecture_list


def lezione_to_lecture(l: unitn.Lezione) -> lecture.Lecture:
    e = Event()
    e.name = l['nome_insegnamento']
    e.description = l['name_original']
    e.begin = l['timestamp_start']
    e.end = l['timestamp_end']
    e.location = l['aula']
    e.status = "CANCELLED" if l['Annullato'] == "1" else "CONFIRMED"

    l = lecture.Lecture()
    l.event = e

    return l


def list_lezione_to_list_lecture(ll: list[unitn.Lezione]) -> list[lecture.Lecture]:
    res: list[lecture.Lecture] = []
    for lez in ll:
        res.append(lezione_to_lecture(lez))

    return res


def attivita_to_course(a: unitn.Attivita) -> course.Course:
    c = course.Course()
    c.name = a['nome_insegnamento']
    c.university = utils.University.UNITN
    c.id = a['valore']
    c.professor_name = a['docente']
    return c


def list_attivita_to_list_courses(la: list[unitn.Attivita]) -> list[course.Course]:
    res: list[course.Course] = []
    for a in la:
        res.append(attivita_to_course(a))
    return res
