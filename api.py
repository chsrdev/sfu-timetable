import json
from pathlib import Path
from urllib.parse import quote

import requests


TIMETABLE_API_URL = "https://edu.sfu-kras.ru/api/timetable/get"
GROUPS_FILE = Path(__file__).with_name("groups.json")


def load_groups(path: Path = GROUPS_FILE) -> list[dict]:
    """Загружает каталог групп, полученный от SFU."""
    with path.open("r", encoding="utf-8") as file:
        groups = json.load(file)

    if not isinstance(groups, list):
        raise ValueError("groups.json должен содержать список групп")

    return groups


def build_timetable_url(group_name: str) -> str:
    """Строит URL API SFU из точного имени группы из groups.json."""
    if not isinstance(group_name, str) or not group_name.strip():
        raise ValueError("Имя группы не может быть пустым")

    # SFU использует именно такой формат: /get&target=...
    return f"{TIMETABLE_API_URL}&target={quote(group_name, safe='')}"


def find_group(group_name: str, groups: list[dict] | None = None) -> dict:
    """Возвращает группу только если она есть в официальном каталоге."""
    groups = load_groups() if groups is None else groups

    for group in groups:
        if group.get("name") == group_name:
            return group

    raise ValueError(f"Группа не найдена в groups.json: {group_name}")


def fetch_timetable(url: str):
    result = requests.get(
        url,
        timeout=15,
    )
    result.raise_for_status()
    return result.json()


def fetch_group_timetable(group_name: str):
    """Проверяет группу в каталоге, строит URL и получает расписание."""
    find_group(group_name)
    return fetch_timetable(build_timetable_url(group_name))
