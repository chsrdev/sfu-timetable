import argparse
import hashlib
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

from dotenv import load_dotenv

from api import build_timetable_url, find_group, fetch_timetable
from calendar_tools import load_old_calendar, get_past_events, create_calendar
from date_tools import get_week_number
from lessons_generator import generate_lessons


load_dotenv()

TZ = timezone(timedelta(hours=7))
PROJECT_DIR = Path(__file__).parent
DEFAULT_CALENDARS_DIR = PROJECT_DIR / "calendars"


def get_schedule_months() -> int:
    value = os.getenv("SCHEDULE_MONTHS", "2")
    months = int(value)

    if months < 1:
        raise ValueError("SCHEDULE_MONTHS должен быть не меньше 1")

    return months


def make_calendar_filename(group_name: str) -> str:
    """Создаёт стабильное и безопасное имя файла для группы."""
    readable_name = re.sub(r"[^\w.-]+", "-", group_name, flags=re.UNICODE)
    readable_name = readable_name.strip(".-") or "group"
    digest = hashlib.sha256(group_name.encode("utf-8")).hexdigest()[:10]
    return f"{readable_name}-{digest}.ics"


def get_calendar_path(group_name: str, output_dir: Path | None = None) -> Path:
    output_dir = DEFAULT_CALENDARS_DIR if output_dir is None else Path(output_dir)
    return output_dir / make_calendar_filename(group_name)


def generate_group_calendar(
    group_name: str,
    output_path: Path | str | None = None,
) -> Path:
    """Получает расписание группы и обновляет её ICS-календарь."""
    # Проверяем группу до обращения к API: пользователь не сможет запросить
    # произвольный target, которого нет в официальном каталоге.
    group = find_group(group_name)
    canonical_name = group["name"]

    if output_path is None:
        output = get_calendar_path(canonical_name)
    else:
        output = Path(output_path)

    output.parent.mkdir(parents=True, exist_ok=True)
    schedule_months = get_schedule_months()
    today = datetime.now(TZ).date()

    print()
    print("======================================")
    print("      SFU TIMETABLE UPDATE")
    print("======================================")
    print(f"Группа: {canonical_name}")
    print(f"Сегодня: {today}")
    print(f"Текущая неделя: {get_week_number(today)}")

    timetable_url = build_timetable_url(canonical_name)
    timetable = fetch_timetable(timetable_url)

    old_calendar = load_old_calendar(str(output))
    past_events = get_past_events(old_calendar, today)
    print(f"Старых событий сохранено: {len(past_events)}")

    future_end = today + timedelta(days=schedule_months * 31)
    future_lessons = generate_lessons(
        timetable,
        today,
        future_end,
        TZ,
    )
    print(f"Новых событий создано: {len(future_lessons)}")

    calendar = create_calendar(past_events, future_lessons, TZ)
    temporary_output = Path(f"{output}.tmp")

    try:
        temporary_output.write_bytes(calendar.to_ical())
        os.replace(temporary_output, output)
    finally:
        if temporary_output.exists():
            temporary_output.unlink()

    print(f"Календарь обновлён: {output}")
    print(f"Расписание загружено до: {future_end}")
    print("======================================")

    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Генерация ICS-календаря для группы SFU"
    )
    parser.add_argument(
        "--group",
        default=os.getenv("GROUP_NAME"),
        help=(
            "Точное имя группы из groups.json, например: "
            'КИ26-16/2Б (2 подгруппа)'
        ),
    )
    parser.add_argument(
        "--output",
        help="Необязательный путь к ICS-файлу",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.group:
        raise SystemExit(
            "Укажите группу через --group или GROUP_NAME в .env. "
            "Используйте точное имя из groups.json."
        )

    generate_group_calendar(args.group, args.output)


if __name__ == "__main__":
    main()
