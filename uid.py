import hashlib


def make_uid(lesson, lesson_date) -> str:
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


    hash_value = hashlib.md5(
        raw.encode("utf-8")
    ).hexdigest()

    return f"{hash_value}@sfu-timetable"