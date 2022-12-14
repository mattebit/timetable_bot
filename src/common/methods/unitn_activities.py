from common.classes.unitn import Attivita
from typing import List, TypedDict, cast
import json
import requests
import datetime

UNITN_COMBO_ENDPOINT = "https://easyacademy.unitn.it/AgendaStudentiUnitn/combo.php"


def filter_activities(activities: list[Attivita], filter_by: str) -> list[Attivita]:
    res = []
    for act in activities:
        if filter_by in act['nome_insegnamento']:
            res.append(act)
    return res


def fetch_activities(max_results: int = 5) -> list[Attivita]:
    year = str(datetime.date.today().year)
    url = UNITN_COMBO_ENDPOINT + f"?sw=ec_&aa={year}&page=attivita"

    resp = requests.request(
        method="GET",
        url=UNITN_COMBO_ENDPOINT + "?sw=ec_&aa=2022&page=attivita"
    )

    # clean output
    resp = resp.text.split('var elenco_attivita = ')[1]  # has js inside
    resp = resp[0:len(resp)-3]  # has a trailing ";"

    l = json.loads(resp)
    activity_list = []
    c = 0

    for i in l:
        if c >= max_results:
            break
        activity_list.append(cast(Attivita, i))
        c += 1
    return activity_list