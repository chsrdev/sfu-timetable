from date_tools import get_week_number, parse_unique_date, parse_date_range, clean_place
from datetime import datetime, timedelta
from uid import make_uid

def generate_lessons(timetable, start_date, end_date, TZ):
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
            # Пропускаем историю (т.к. лекций в семестре больше нет, потом добавить)
            if 'история' in lesson['subject'].lower():
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