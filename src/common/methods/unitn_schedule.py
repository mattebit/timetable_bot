import datetime

import requests
from googleapiclient.discovery import Resource

from src.common.classes.unitn import Lezione, GridCallResponse
from src.common.methods.google import addEvent
from src.common.methods.utils import get_lecture_start_end_timestamps

# By setting all_events to 1 you will get all the events of the course
UNITN_GRID_ENDPOINT = "https://easyacademy.unitn.it/AgendaStudentiUnitn/grid_call.php"


# the date filters the week activities
def fetch_lectures(attivita_id: str, all_events: bool = False) -> list[Lezione]:
    year = str(datetime.date.today().year)
    date = datetime.date.today().strftime('%d-%m-%Y')  # italian format
    if all_events:
        all_events = 1
    else:
        all_events = 0

    query = f"?view=easycourse&form-type=attivita&include=attivita&anno={year}&attivita%5B%5D={attivita_id}&" \
            f"visualizzazione_orario=cal&date={date}&list=&week_grid_type=-1&col_cells=0&empty_box=0&" \
            f"only_grid=0&highlighted_date=0&faculty_group=0&_lang=en&all_events={all_events}"

    url = UNITN_GRID_ENDPOINT + query

    resp = requests.request(
        method="GET",
        url=url
    )

    j: GridCallResponse = resp.json()

    lecture_list : list[Lezione] = []
    lecture_list = j['celle']

    # Create start and end unix timestamps
    for l in lecture_list:
        start_timestamp, end_timestamp = get_lecture_start_end_timestamps(
            l['ora_inizio'], l['ora_fine'], l['timestamp'])
        l['timestamp_start'] = start_timestamp
        l['timestamp_end'] = end_timestamp

    return lecture_list