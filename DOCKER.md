## Docker-деплой Alo.bg Auto-Bump

Этот файл описывает, как развернуть проект в Docker и настроить автоматический запуск скрипта в **09:30 по времени Софии (Europe/Sofia)**.

- **Базовый образ**: `python:3.12-slim`
- **Точка входа контейнера**: `python main.py`
- **Конфигурация**: через внешний `.env` (не попадает в образ)
- **Логи**: монтируются как volume в каталог `logs/`

Рекомендуется сначала настроить **ручной запуск контейнера**, затем добавить один из вариантов расписания.

---

## 1. Подготовка проекта к Docker

- В корне проекта уже добавлен файл `Dockerfile`.
- Файл `.env` **не копируется** в образ и хранится только на хосте.
- Логи пишутся в каталог `logs/`, который удобно монтировать как volume.

Проверьте, что на сервере:

- Установлен Docker: `docker --version`
- Время сервера и/или переменная `TZ` настроены на `Europe/Sofia` (см. варианты ниже).

---

## 2. Сборка Docker-образа

На сервере (или локально, если затем будете пушить образ в registry) выполните:

```bash
cd /opt/alobg
sudo docker build -t alo-auto-bump . Внимание точка в конце!!!!
```

- `alo-auto-bump` — имя образа, вы можете заменить его на любое удобное.

---

## 3. Настройка `.env` для контейнера

Создайте/обновите `.env` рядом с `Dockerfile`:

```env
ALO_LOGIN=your_email@example.com
ALO_PASSWORD=your_password
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Browser settings
BROWSER_HEADLESS=true
```

**Важно:**

- Не добавляйте `.env` в образ, не коммитьте его в git.
- Для контейнера мы будем использовать опцию `--env-file .env`.

---

## 4. Ручной запуск контейнера

Разовый запуск (для теста):

```bash
sudo mkdir -p logs
sudo docker run --rm \
  --name alo-auto-bump-test \
  --env-file .env \
  -v "$(pwd)/logs:/app/logs" \
  alo-auto-bump
```

Пояснения:

- `--rm` — контейнер удаляется после завершения работы.
- `--env-file .env` — передаём все переменные окружения из `.env` в контейнер.
- `-v "$(pwd)/logs:/app/logs"` — логи из контейнера будут писаться в локальный каталог `logs/`.

После запуска проверьте:

- наличие сообщений в Telegram;
- содержимое логов в `logs/alo_auto_bump.log`.

---

## 5. Варианты автоматического запуска в 09:30 (Europe/Sofia)

Ниже несколько подходов к расписанию. **Рекомендуемый — cron или systemd на хосте**, которые запускают одноразовый контейнер.

### Вариант 1 (рекомендуемый): cron на хосте, запускающий контейнер

Подходит, если на сервере уже используется cron (Ubuntu/Debian и т.д.).

1. Убедитесь, что часовой пояс сервера установлен на `Europe/Sofia`:

   ```bash
   timedatectl
   # при необходимости:
   sudo timedatectl set-timezone Europe/Sofia
   ```

2. Откройте crontab от имени пользователя, который будет запускать контейнер:

   ```bash
   crontab -e
   ```

3. Добавьте задачу на ежедневный запуск в **09:30**:

   ```cron
   SHELL=/bin/bash
   PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
   TZ=Europe/Sofia

   30 9 * * * cd /opt/alobg && docker run --rm --name alo-auto-bump-cron --env-file .env -v "$(pwd)/logs:/app/logs" alo-auto-bump >> "$(pwd)/logs/cron_docker.log" 2>&1
   ```

   Где:

   - `30 9 * * *` — каждый день в 09:30.
   - `TZ=Europe/Sofia` — гарантирует использование времени Софии для cron.
   - Логи cron-запуска пишутся в `logs/cron_docker.log`.

**Плюсы:**

- Контейнер живёт только во время выполнения скрипта.
- Простая отладка, понятные логи.

**Минусы:**

- Требует установленного и настроенного cron на хосте.

---

### Вариант 2: systemd timer на хосте, запускающий контейнер

Подходит, если вы предпочитаете systemd вместо cron.

1. Создайте юнит-файл сервиса, например `/etc/systemd/system/alo-auto-bump.service`:

   ```ini
   [Unit]
   Description=Alo.bg auto bump via Docker
   Wants=network-online.target
   After=network-online.target

   [Service]
   Type=oneshot
   WorkingDirectory=/path/to/alobg
   ExecStart=/usr/bin/docker run --rm --name alo-auto-bump-systemd --env-file .env -v %h/alobg/logs:/app/logs alo-auto-bump
   ```

2. Создайте таймер `/etc/systemd/system/alo-auto-bump.timer`:

   ```ini
   [Unit]
   Description=Run Alo.bg auto bump every day at 09:30 (Europe/Sofia)

   [Timer]
   OnCalendar=Europe/Sofia 09:30
   Persistent=true

   [Install]
   WantedBy=timers.target
   ```

3. Перечитайте конфигурацию и включите таймер:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable --now alo-auto-bump.timer
   ```

4. Проверка:

   ```bash
   systemctl list-timers | grep alo-auto-bump
   journalctl -u alo-auto-bump.service -f
   ```

**Плюсы:**

- Глубокая интеграция с systemd, удобный мониторинг через `journalctl`.

**Минусы:**

- Требует прав root/sudo для настройки.

---

### Вариант 3: cron внутри Docker-контейнера

Этот вариант **менее рекомендуем**, но возможен, если вы хотите, чтобы контейнер сам управлял расписанием.

Идея:

- контейнер постоянно запущен;
- внутри работает `cron`, который каждый день в 09:30 запускает `python /app/main.py`.

Примерно это можно реализовать так:

1. Расширить `Dockerfile`, установив `cron` и добавив cron-задачу:

   ```dockerfile
   RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

   # Добавляем cron-задачу
   RUN echo "30 9 * * * cd /app && python main.py >> /app/logs/cron_in_container.log 2>&1" > /etc/cron.d/alo-auto-bump && \
       chmod 0644 /etc/cron.d/alo-auto-bump && \
       crontab /etc/cron.d/alo-auto-bump

   CMD ["cron", "-f"]
   ```

2. Запустить контейнер один раз и оставить работать:

   ```bash
   docker run -d \
     --name alo-auto-bump-cron-in-container \
     --env-file .env \
     -v "$(pwd)/logs:/app/logs" \
     alo-auto-bump
   ```

**Плюсы:**

- Хост не знает о расписании — вся логика внутри контейнера.

**Минусы:**

- Контейнер постоянно живёт, хотя скрипт нужен раз в день.
- Сложнее мониторить и обновлять cron-конфигурацию.

---

## 6. Рекомендации по выбору варианта

- **Если у вас обычный VPS с root-доступом и cron уже используется** — выбирайте **Вариант 1 (cron на хосте)**.
- **Если инфраструктура стандартизирована на systemd timers** — выбирайте **Вариант 2**.
- **Вариант 3 (cron внутри контейнера)** нужен только если вы сознательно хотите изолировать расписание от хоста.

Во всех вариантах:

- Секреты (логин/пароль, токены Telegram) хранятся только в `.env` на хосте.
- Время выполнения ориентировано на `Europe/Sofia` (через системный часовой пояс и/или `TZ`).

