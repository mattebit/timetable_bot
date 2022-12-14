from typing import List, TypedDict, cast
import json


class Attivita(TypedDict):
    periodi: list
    pub_type: str
    label: str
    valore: str
    nome_insegnamento: str
    id: str
    docente: str
    codice_combinato: str
    default_grid: str
    facolta_code: str
    facolta_id: str