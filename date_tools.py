import re
from datetime import date

WEEK_1_START = date(2026, 8, 31)

def parse_date(day, month, year) -> date |  None:
    if year < 100:
        year += 2000

    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_unique_date(place) -> date | None:
    """
    Ищет:

        только 16.09.2026 г.
        только 03.10. 2026 г.
    """

    match = re.search(
        r'только\s+(\d{1,2})\.(\d{1,2})\.?\s*(\d{2,4})',
        place,
        re.IGNORECASE
    )

    if not match:
        return None

    day, month, year = map(int, match.groups())

    return parse_date(day, month, year)


def parse_date_range(place) -> tuple:
    """
    Ищет:

        с 12.10.2026 по 30.12.2026
    """

    match = re.search(
        r'с\s+(\d{1,2})\.(\d{1,2})\.?\s*(\d{2,4})'
        r'\s+по\s+(\d{1,2})\.(\d{1,2})\.?\s*(\d{2,4})',
        place,
        re.IGNORECASE
    )

    if not match:
        return None, None

    (
        start_day,
        start_month,
        start_year,
        end_day,
        end_month,
        end_year
    ) = map(int, match.groups())

    start_date = parse_date(
        start_day,
        start_month,
        start_year
    )

    end_date = parse_date(
        end_day,
        end_month,
        end_year
    )

    return start_date, end_date


def clean_place(place) -> str:
    """
    Убирает служебные пометки:

        (только 16.09.2026 г.)
        (с 12.10.2026 по 30.12.2026)
    """

    place = re.sub(
        r'\s*\([^)]*только[^)]*\)',
        '',
        place,
        flags=re.IGNORECASE
    )

    place = re.sub(
        r'\s*\([^)]*с\s+\d{1,2}\.\d{1,2}\.?\s*\d{2,4}'
        r'\s+по\s+\d{1,2}\.\d{1,2}\.?\s*\d{2,4}[^)]*\)',
        '',
        place,
        flags=re.IGNORECASE
    )

    return place.strip()

def get_week_number(day) -> int:
    """
    Определяет номер недели:

        31.08–06.09 → 1
        07.09–13.09 → 2
        14.09–20.09 → 1
        21.09–27.09 → 2
        ...
    """

    weeks_passed = (day - WEEK_1_START).days // 7

    return weeks_passed % 2 + 1