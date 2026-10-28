import requests

def fetch_timetable(URL: str):
    result = requests.get(
        URL,
        verify=False,
        timeout=15
    )

    if result.status_code != 200:
        print(f"Ошибка API: {result.status_code}")
        return None

    return result.json()