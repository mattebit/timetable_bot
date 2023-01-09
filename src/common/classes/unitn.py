from datetime import datetime
from typing import TypedDict


class Attivita(TypedDict):
    periodi: list
    pub_type: str
    label: str
    valore: str  # Actual ID of the activity
    nome_insegnamento: str
    id: str
    docente: str
    codice_combinato: str
    default_grid: str
    facolta_code: str
    facolta_id: str


class Lezione(TypedDict):
    codice_insegnamento: str
    nome_insegnamento: str
    name_original: str
    codice_docente: str
    docente: str
    mail_docente: str
    percorso_didattico: str
    id: str
    timestamp: int
    data: str
    codice_aula: str
    codice_sede: str
    aula: str
    tipo: str
    ora_inizio: str
    ora_fine: str
    Annullato: str
    # Custom
    timestamp_start: datetime
    timestamp_end: datetime


class GridCallResponse(TypedDict):
    day: str
    data: str
    data_timestamp: int
    first_day: str
    last_day: str
    first_day_timestamp: int
    last_day_timestamp: int
    aa: str
    attivita: list[str]
    celle: list[Lezione]
