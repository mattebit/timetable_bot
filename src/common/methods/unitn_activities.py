import datetime
import json
from typing import cast

import requests
from common.classes.unitn import Attivita

UNITN_COMBO_ENDPOINT = "https://easyacademy.unitn.it/AgendaStudentiUnitn/combo.php"


def filter_activities(activities: list[Attivita], filter_by: str) -> list[Attivita]:
    res = []
    for act in activities:
        if filter_by in act['nome_insegnamento']:
            res.append(act)
    return res


def fetch_activities() -> list[Attivita]:
    year = str(datetime.date.today().year)
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
        activity_list.append(cast(Attivita, i))

    print(activity_list[0])
    return activity_list
