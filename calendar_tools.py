import os
from datetime import datetime, date, timedelta
from icalendar import Calendar, Event

def load_old_calendar(OUTPUT: str):
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


def create_calendar(past_events, future_lessons, TZ):

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
