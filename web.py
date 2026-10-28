from flask import Flask, abort, jsonify, render_template, request, send_file, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

from api import find_group, load_groups
from main import generate_group_calendar, make_calendar_filename


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)


@app.after_request
def add_local_cors(response):
    origin = request.headers.get("Origin")
    if origin in {"http://localhost:3000", "http://127.0.0.1:3000"}:
        response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


def get_group_catalog() -> list[dict]:
    """Возвращает группы без дублирования по подгруппам."""
    groups = {}

    for item in load_groups():
        name = item.get("name", "").strip()
        if not name:
            continue

        subgroup = None
        if name.endswith(")") and " (" in name:
            base_name, subgroup_text = name.rsplit(" (", 1)
            subgroup_text = subgroup_text.removesuffix(")")
            if subgroup_text.endswith("подгруппа"):
                subgroup = subgroup_text.removesuffix(" подгруппа")
                name = base_name

        entry = groups.setdefault(
            name,
            {
                "name": name,
                "institute": item.get("institute", ""),
                "course": item.get("course", ""),
                "subgroups": [],
            },
        )

        if subgroup and subgroup not in entry["subgroups"]:
            entry["subgroups"].append(subgroup)

    result = list(groups.values())
    result.sort(key=lambda item: (item["institute"], item["course"], item["name"]))
    return result


def get_group_by_calendar_id(calendar_id: str) -> str | None:
    for item in load_groups():
        group_name = item.get("name", "")
        filename = make_calendar_filename(group_name)
        if filename.removesuffix(".ics") == calendar_id:
            return group_name
    return None


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/groups")
def groups_api():
    return jsonify(get_group_catalog())


@app.get("/api/calendar-link")
def calendar_link():
    group_name = request.args.get("group", "")

    try:
        group = find_group(group_name)
    except ValueError:
        return jsonify({"error": "Группа не найдена"}), 404

    calendar_id = make_calendar_filename(group["name"]).removesuffix(".ics")
    return jsonify({
        "group": group["name"],
        "url": url_for("calendar", calendar_id=calendar_id, _external=True),
    })


@app.get("/calendar/<calendar_id>.ics")
def calendar(calendar_id: str):
    group_name = get_group_by_calendar_id(calendar_id)
    if group_name is None:
        abort(404, description="Группа не найдена")

    try:
        path = generate_group_calendar(group_name)
    except Exception as error:
        app.logger.exception("Не удалось создать календарь для %s", group_name)
        abort(502, description=f"Не удалось получить расписание: {error}")

    response = send_file(
        path,
        mimetype="text/calendar; charset=utf-8",
        as_attachment=False,
        download_name=path.name,
        max_age=300,
    )
    response.headers["Content-Disposition"] = "inline"
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
