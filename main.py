import requests
import re
import os
from dotenv import load_dotenv
from datetime import datetime, date, timezone, timedelta
from icalendar import Calendar, Event

load_dotenv()
URL = os.getenv("URL")
if URL is None:
    print("URL не найдена в .env")
    exit()
TZ = timezone(timedelta(hours=7))
WEEK_1_START = date(2026, 8, 31)
SCHEDULE_MONTHS = os.getenv("SCHEDULE_MONTHS")
if SCHEDULE_MONTHS is None:
    SCHEDULE_MONTHS = 1
else:
    SCHEDULE_MONTHS = int(SCHEDULE_MONTHS)
OUTPUT = os.getenv("ICS_FILE_PATH")


# =========================================================
# API
# =========================================================

def fetch_timetable():
    result = requests.get(
        URL,
        verify=False,
        timeout=15
    )

    if result.status_code != 200:
        print(f"Ошибка API: {result.status_code}")
        return None

    return result.json()


# =========================================================
# Вспомогательные функции дат
# =========================================================

def parse_date(day, month, year):
    if year < 100:
        year += 2000

    try:
        return date(year, month, day)
    except ValueError:
        return None


def parse_unique_date(place):
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


def parse_date_range(place):
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


def clean_place(place):
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


# =========================================================
# Недели
# =========================================================

def get_week_number(day):
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


# =========================================================
# UID
# =========================================================

def make_uid(lesson, lesson_date):
    """
    Создаёт стабильный UID для события.

    Благодаря этому календарь понимает,
    что это именно та же самая пара.
    """

    raw = (
        f'{lesson["subject"]}|'
        f'{lesson["teacher"]}|'
        f'{lesson["type"]}|'
        f'{lesson_date}|'
        f'{lesson["time"]}'
    )

    import hashlib

    hash_value = hashlib.md5(
        raw.encode("utf-8")
    ).hexdigest()

    return f"{hash_value}@sfu-timetable"


# =========================================================
# Генерация занятий
# =========================================================

def generate_lessons(timetable, start_date, end_date):
    """
    Генерирует ВСЕ занятия между start_date и end_date.
    """

    timetable = timetable["timetable"]

    result = []

    current_date = start_date

    while current_date <= end_date:

        current_week = get_week_number(current_date)
        current_day = current_date.weekday() + 1

        for lesson in timetable:

            # Онлайн, русский язык пропускаем
            if 'ЭИОС' in lesson['place']:
                continue
            if 'русский язык' in lesson['subject']:
                continue

            # День недели не совпадает
            if int(lesson['day']) != current_day:
                continue

            # Неделя не совпадает
            if lesson['week'] != str(current_week):
                continue

            # -----------------------------------------
            # Только конкретная дата
            # -----------------------------------------

            unique_date = parse_unique_date(
                lesson['place']
            )

            if unique_date is not None:

                if current_date != unique_date:
                    continue

            # -----------------------------------------
            # Период "с ... по ..."
            # -----------------------------------------

            period_start, period_end = parse_date_range(
                lesson['place']
            )

            if period_start is not None:

                if current_date < period_start:
                    continue

                if period_end is not None:
                    if current_date > period_end:
                        continue

            # -----------------------------------------
            # Время
            # -----------------------------------------

            start_hour, start_minute = map(
                int,
                lesson['time'][0:5].split(':')
            )

            start_at = datetime(
                current_date.year,
                current_date.month,
                current_date.day,
                start_hour,
                start_minute,
                tzinfo=TZ
            )

            result.append({
                'uid': make_uid(
                    lesson,
                    current_date
                ),

                'start_at': start_at,

                'subject': lesson['subject'],

                'type': lesson['type'],

                'teacher': lesson['teacher'],

                'place': clean_place(
                    lesson['place']
                )
            })

        current_date += timedelta(days=1)

    return result


# =========================================================
# Работа с существующим календарём
# =========================================================

def load_old_calendar():
    """
    Загружает существующий .ics.

    Если файла нет — создаёт пустой календарь.
    """

    if not os.path.exists(OUTPUT):
        return Calendar()

    try:
        with open(OUTPUT, 'rb') as f:
            return Calendar.from_ical(f.read())

    except Exception as e:
        print(f"Не удалось прочитать старый календарь: {e}")
        return Calendar()


def extract_event_date(event):
    """
    Получает дату начала события.
    """

    try:
        dt = event.get('dtstart').dt

        if isinstance(dt, datetime):
            return dt.date()

        if isinstance(dt, date):
            return dt

    except Exception:
        pass

    return None


def get_past_events(calendar, today):
    """
    Оставляет только события до сегодняшнего дня.

    Всё, что сегодня или позже — будет пересоздано.
    """

    result = []

    for component in calendar.walk():

        if component.name != 'VEVENT':
            continue

        event_date = extract_event_date(component)

        if event_date is None:
            continue

        if event_date < today:
            result.append(component)

    return result


# =========================================================
# Создание нового календаря
# =========================================================

def create_calendar(past_events, future_lessons):

    cal = Calendar()

    cal.add(
        'prodid',
        '-//sfu-timetable//SFU//RU'
    )

    cal.add(
        'version',
        '2.0'
    )

    # -----------------------------------------
    # Старые события
    # -----------------------------------------

    for event in past_events:
        cal.add_component(event)

    # -----------------------------------------
    # Новые события
    # -----------------------------------------

    for lesson in future_lessons:

        event = Event()

        event.add(
            'uid',
            lesson['uid']
        )

        event.add(
            'summary',
            f'{lesson["subject"]}, {lesson["place"]}'
        )

        event.add(
            'description',
            f'{lesson["type"]}, {lesson["teacher"]}'
        )

        event.add(
            'dtstart',
            lesson['start_at']
        )

        event.add(
            'dtend',
            lesson['start_at'] + timedelta(minutes=95)
        )

        event.add(
            'dtstamp',
            datetime.now(TZ)
        )

        cal.add_component(event)

    return cal


# =========================================================
# MAIN
# =========================================================

def main():

    today = datetime.now(TZ).date()

    print()
    print("======================================")
    print("      SFU TIMETABLE UPDATE")
    print("======================================")

    print(f"Сегодня: {today}")
    print(f"Текущая неделя: {get_week_number(today)}")

    # -----------------------------------------
    # Получаем актуальное расписание SFU
    # -----------------------------------------

    timetable = fetch_timetable()

    if timetable is None:
        print("API недоступен. Старый календарь не изменён.")
        return

    # -----------------------------------------
    # Загружаем старый календарь
    # -----------------------------------------

    old_calendar = load_old_calendar()

    # -----------------------------------------
    # Забираем историю
    # -----------------------------------------

    past_events = get_past_events(
        old_calendar,
        today
    )

    print(
        f"Старых событий сохранено: "
        f"{len(past_events)}"
    )

    # -----------------------------------------
    # Конец нового расписания
    # -----------------------------------------

    future_end = today + timedelta(
        days=SCHEDULE_MONTHS * 31
    )

    # -----------------------------------------
    # Генерируем актуальное будущее
    # -----------------------------------------

    future_lessons = generate_lessons(
        timetable,
        today,
        future_end
    )

    print(
        f"Новых событий создано: "
        f"{len(future_lessons)}"
    )

    # -----------------------------------------
    # Создаём календарь
    # -----------------------------------------

    calendar = create_calendar(
        past_events,
        future_lessons
    )

    # -----------------------------------------
    # Безопасно заменяем файл
    # -----------------------------------------

    temp_file = OUTPUT + '.tmp'

    with open(temp_file, 'wb') as f:
        f.write(calendar.to_ical())

    os.replace(
        temp_file,
        OUTPUT
    )

    print()
    print("Календарь обновлён.")
    print(f"До: {future_end}")
    print(f"Файл: {OUTPUT}")
    print("======================================")


if __name__ == "__main__":
    main()