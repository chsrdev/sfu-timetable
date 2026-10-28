import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from calendar_tools import load_old_calendar, get_past_events, create_calendar
from date_tools import get_week_number
from lessons_generator import generate_lessons
from api import fetch_timetable

load_dotenv()

TZ = timezone(timedelta(hours=7))


# =========================================================
# MAIN
# =========================================================

def main():
    URL = os.getenv("URL")
    if URL is None:
        print("URL не найден в .env")
        return
    
    SCHEDULE_MONTHS = os.getenv("SCHEDULE_MONTHS")
    if SCHEDULE_MONTHS is None:
        SCHEDULE_MONTHS = 1
    else:
        SCHEDULE_MONTHS = int(SCHEDULE_MONTHS)

    OUTPUT = os.getenv("ICS_FILE_PATH")
    if OUTPUT is None:
        print("OUTPUT не найден в .env")
        return
    
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

    timetable = fetch_timetable(URL)

    if timetable is None:
        print("API недоступен. Старый календарь не изменён.")
        return

    # -----------------------------------------
    # Загружаем старый календарь
    # -----------------------------------------

    old_calendar = load_old_calendar(OUTPUT)

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
        future_end,
        TZ
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
        future_lessons,
        TZ
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