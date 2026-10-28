# SFU Calendar

## Локальный запуск

В первом терминале запусти backend:

```powershell
.venv\bin\python.exe web.py
```

Backend будет доступен на `http://127.0.0.1:8000`.

Во втором терминале установи зависимости frontend и запусти Next.js:

```powershell
cd frontend
npm install
npm run dev
```

Открой `http://localhost:3000`.

Если backend использует другой адрес, создай `frontend/.env.local` на основе `.env.local.example`.

## Git

В коммит не должны попадать `.env`, `calendars/`, `node_modules/` и `.next/`. Они уже добавлены в `.gitignore`.
