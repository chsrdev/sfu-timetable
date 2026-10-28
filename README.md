# SFU Calendar

## Локальный запуск

Backend:

```powershell
.venv\bin\python.exe web.py
```

Frontend в другом окне:

```powershell
cd frontend
npm install
npm run dev
```

Откройте `http://localhost:3000`.

## Запуск на VPS через Docker

Ниже пример для Ubuntu 24.04. Так как на сервере уже работает другой сайт на PM2, этот проект будет доступен через порт 8080. Порт 80 и существующий сайт не затрагиваются.

### 1. Подключиться к серверу

```bash
ssh root@SERVER_IP
```

### 2. Установить Docker

```bash
apt update && apt upgrade -y
apt install -y git ufw
curl -fsSL https://get.docker.com | sh
systemctl enable --now docker
```

Открыть SSH и HTTP:

```bash
ufw allow OpenSSH
ufw allow 8080/tcp
ufw --force enable
```

### 3. Скачать проект

```bash
git clone YOUR_REPOSITORY_URL sfu-timetable
cd sfu-timetable
cp .env.example .env
```

Откройте `.env` и проверьте:

```bash
nano .env
```

Минимально должно быть:

```env
SCHEDULE_MONTHS=2
NEXT_PUBLIC_CONTACT_URL=https://t.me/anonimnyye_voprosys_bot?start=7xa2BTnC
```

### 4. Запустить приложение

```bash
docker compose up -d --build
```

Проверить контейнеры:

```bash
docker compose ps
docker compose logs -f --tail=100
```

Сайт будет доступен по адресу:

```text
http://SERVER_IP:8080
```

Проверка backend:

```bash
curl http://SERVER_IP:8080/health
```

Ожидаемый ответ:

```json
{"status":"ok"}
```

### 5. Обновить проект после изменений

```bash
git pull
docker compose up -d --build
```

### 6. Остановить приложение

```bash
docker compose down
```

Сгенерированные `.ics` сохраняются в Docker volume `sfu-timetable_calendars` и не пропадают при пересборке контейнеров.

## После покупки домена

Не меняйте текущий PM2-сайт. После покупки домена добавьте отдельный reverse proxy на `127.0.0.1:8080` в конфигурации существующего Nginx, направьте A-запись домена на IP сервера и добавьте HTTPS через Certbot. До покупки домена приложение работает по `http://SERVER_IP:8080`.


