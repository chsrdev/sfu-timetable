import json
from pathlib import Path

import requests


GROUPS_URL = "https://edu.sfu-kras.ru/api/timetable/get_insts"
OUTPUT_FILE = Path(__file__).with_name("groups.json")


response = requests.get(GROUPS_URL, timeout=15)
response.raise_for_status()

with OUTPUT_FILE.open("w", encoding="utf-8") as file:
    json.dump(response.json(), file, ensure_ascii=False, indent=2)

print(f"Группы сохранены в {OUTPUT_FILE}")
