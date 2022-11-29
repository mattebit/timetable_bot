from typing import Any, List, TypedDict, cast
import json

class Attivita(TypedDict):
  periodi: list
  pub_type: str
  label: str
  valore: str
  id: str
  docente: str
  codice_combinato: str
  default_grid: str
  facolta_code: str
  facolta_id: str

class Combo_activities_response(TypedDict):
  list : list[Attivita]

test = json.loads(open("combo_attivita.json", "r").read())

test2 : Attivita = cast(Attivita, test[0])

print(type(test[0]))
print(type(test2))

test2["facolta_id"] = "123"

#print(test2.label)
