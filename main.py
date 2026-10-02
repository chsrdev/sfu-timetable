import requests, re, os
from datetime import datetime, date, timezone, timedelta
from icalendar import Calendar, Event

URL = "https://edu.sfu-kras.ru/api/timetable/get&target=%D0%9A%D0%9826-16/2%D0%91%20(2%20%D0%BF%D0%BE%D0%B4%D0%B3%D1%80%D1%83%D0%BF%D0%BF%D0%B0)"
TZ  = timezone(timedelta(hours=7))
ODD_WEEK_START = date(2026, 9, 1)
OUTPUT = "/var/www/sfu-timetable/schedule.ics"


def fetch_timetable():
    result = requests.get(URL, verify=False, timeout=15)
    if result.status_code != 200:
        print(result)
        return
    return result.json()


def parse_unique_date(place):
    if 'только' not in place.lower():
        return None

    match = re.search(
        r'только\s+(\d{1,2})\.(\d{1,2})\.\s*(\d{2,4})',
        place,
        re.IGNORECASE
    )

    if not match:
        return None

    day, month, year = map(int, match.groups())

    if year < 100:
        year += 2000

    try:
        return date(year, month, day)
    except ValueError:
        return None



def clean_place(place):
    return re.sub(
        r'\s*\([^)]*только[^)]*\)',
        '',
        place,
        flags=re.IGNORECASE
    ).strip()


def process_timetable(timetable):
    # start_at : datetime
    # subject  : str
    # type     : str
    # teacher  : str
    # place    : str

    timetable = timetable["timetable"]
    result = []
    today = datetime.now(TZ).date()
    curr_week = ((today - ODD_WEEK_START).days // 7) % 2 + 1
    curr_day = today.weekday() + 1

    for lesson in timetable:
        # обработка онлайн занятий
        if 'ЭИОС' in lesson['place']:
            continue

        record = {}
        date_delta = int(lesson['day']) - curr_day
        if lesson['week'] != str(curr_week):
            date_delta += 7

        lesson_date = today + timedelta(days=date_delta)
        start_hour, start_minute = map(int, lesson['time'][0:5].split(':'))

        # обработка уникальных уроков
        unique_date = parse_unique_date(lesson['place'])
        if unique_date is not None:
            if unique_date < today:
                continue
            lesson_date = unique_date

        record['start_at'] = datetime(
            lesson_date.year, lesson_date.month, lesson_date.day,
            start_hour, start_minute, tzinfo=TZ
        )
        record['subject'] = lesson['subject']
        record['type'] = lesson['type']
        record['teacher'] = lesson['teacher']
        record['place'] = clean_place(lesson['place'])

        result.append(record)

    return result


def create_calendar(lessons):
    cal = Calendar()
    cal.add('prodid', '-//sfu-timetable//SFU//RU')
    cal.add('version', '2.0')

    for lesson in lessons:
        event = Event()
        event.add('summary', f'{lesson["subject"]}, {lesson["place"]}')
        event.add('description', f'{lesson["type"]}, {lesson["teacher"]}')
        event.add('dtstart', lesson['start_at'])
        event.add('dtend', lesson['start_at'] + timedelta(minutes=95))
        event.add('dtstamp', datetime.now(TZ))
        cal.add_component(event)

    return cal


def main():
    timetable = fetch_timetable()
    lessons = process_timetable(timetable)
    calendar = create_calendar(lessons)

    temp_file = OUTPUT + '.tmp'

    with open(temp_file, 'wb') as f:
        f.write(calendar.to_ical())

    os.replace(temp_file, OUTPUT)


if __name__ == "__main__":
    main()