# Инструкция по развёртыванию на VPS Ubuntu

Подробная инструкция по настройке автоматического запуска скрипта на сервере VPS Ubuntu.

## Предварительные требования

- VPS сервер с Ubuntu 20.04 или новее
- Доступ по SSH с правами sudo
- Python 3.10 или выше

## Шаг 1: Подключение к серверу

Подключитесь к вашему VPS серверу по SSH:

```bash
ssh username@your_server_ip
```

## Шаг 2: Обновление системы

Обновите список пакетов и установите обновления:

```bash
sudo apt update
sudo apt upgrade -y
```

## Шаг 3: Установка Python и необходимых пакетов

Установите Python 3, pip и необходимые системные зависимости:

```bash
sudo apt install -y python3 python3-pip python3-venv git
```

Проверьте версию Python (должна быть 3.10 или выше):

```bash
python3 --version
```

## Шаг 4: Создание пользователя для скрипта (рекомендуется)

Создайте отдельного пользователя для запуска скрипта (опционально, но рекомендуется для безопасности):

```bash
sudo adduser alobg
```

Следуйте инструкциям для установки пароля (можно оставить пустым, если не планируете использовать пароль).

**Важно:** Если вы используете существующего пользователя без прав sudo (например, `bot-user`), это нормально. Скрипт может работать и без прав администратора. Просто пропустите следующую команду.

Добавьте пользователя в группу sudo (только если нужны права sudo для установки системных зависимостей):

```bash
sudo usermod -aG sudo alobg
```

Переключитесь на нового пользователя:

```bash
sudo su - alobg
```

**Примечание:** Если вы работаете от пользователя без прав sudo, продолжайте работу от его имени. Установка системных зависимостей Playwright может потребовать помощи администратора, но часто не требуется.

## Шаг 5: Загрузка проекта на сервер

### Вариант 1: Клонирование из Git репозитория

Если проект находится в Git репозитории:

```bash
cd ~
git clone <your_repository_url> alobg
cd alobg
```

### Вариант 2: Загрузка через SCP

Если проект находится локально, загрузите его на сервер:

**На вашем локальном компьютере:**

```bash
scp -r /path/to/alobg username@your_server_ip:~/
```

**На сервере:**

```bash
cd ~
cd alobg
```

### Вариант 3: Создание проекта вручную

Создайте структуру проекта вручную и загрузите файлы:

```bash
mkdir -p ~/alobg
cd ~/alobg
# Загрузите все файлы проекта сюда
```

## Шаг 6: Настройка виртуального окружения

Создайте и активируйте виртуальное окружение:

```bash
cd ~/alobg
python3 -m venv venv
source venv/bin/activate
```

Установите зависимости:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Установите браузер Chromium для Playwright:

```bash
playwright install chromium
```

**Важно:** Команда `playwright install-deps chromium` требует прав `sudo` для установки системных зависимостей.

**Если у вас нет прав sudo:**

1. **Попробуйте запустить скрипт без установки зависимостей** - часто Playwright работает и без них:
   ```bash
   python main.py
   ```

2. **Если скрипт не запускается**, попросите администратора сервера установить зависимости через apt-get:
   ```bash
   # Администратор должен выполнить:
   sudo apt-get update
   sudo apt-get install -y libnspr4 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 libatspi2.0-0 libxshmfence1
   ```

   **Примечание:** Команда `playwright install-deps chromium` работает только если playwright установлен глобально или если выполняется из виртуального окружения. Для системных зависимостей лучше использовать `apt-get`.

3. **Или установите зависимости вручную** (если есть доступ к root через другого пользователя):
   ```bash
   # Войдите как root или пользователь с sudo
   sudo apt-get update
   sudo apt-get install -y \
     libnss3 \
     libnspr4 \
     libatk1.0-0 \
     libatk-bridge2.0-0 \
     libcups2 \
     libdrm2 \
     libdbus-1-3 \
     libxkbcommon0 \
     libxcomposite1 \
     libxdamage1 \
     libxfixes3 \
     libxrandr2 \
     libgbm1 \
     libasound2 \
     libpango-1.0-0 \
     libcairo2 \
     libatspi2.0-0 \
     libxshmfence1
   ```

   **Примечание:** Если система использует пакеты с суффиксом `t64` (Ubuntu 24.04+), используйте эту команду:
   ```bash
   sudo apt-get update
   sudo apt-get install -y \
     libnss3 \
     libnspr4 \
     libatk1.0-0t64 \
     libatk-bridge2.0-0t64 \
     libcups2t64 \
     libdrm2 \
     libdbus-1-3 \
     libxkbcommon0 \
     libxcomposite1 \
     libxdamage1 \
     libxfixes3 \
     libxrandr2 \
     libgbm1 \
     libasound2t64 \
     libpango-1.0-0 \
     libcairo2 \
     libatspi2.0-0t64 \
     libxshmfence1
   ```

**Примечание:** В большинстве случаев для работы Playwright в headless режиме достаточно только `playwright install chromium`, без установки системных зависимостей.

## Шаг 7: Настройка переменных окружения

Создайте файл `.env` на основе примера:

```bash
cp .env.example .env
nano .env
```

Заполните файл `.env` своими данными:

```env
ALO_LOGIN=your_email@example.com
ALO_PASSWORD=your_password
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Browser settings
BROWSER_HEADLESS=true
```

Сохраните файл (в nano: `Ctrl+O`, затем `Enter`, затем `Ctrl+X`).

Убедитесь, что файл `.env` имеет правильные права доступа:

```bash
chmod 600 .env
```

## Шаг 8: Тестовый запуск

Проверьте, что скрипт работает корректно:

```bash
cd ~/alobg
source venv/bin/activate
python main.py
```

Если всё работает правильно, вы увидите логи выполнения и получите отчёт в Telegram.

## Шаг 9: Настройка часового пояса

Убедитесь, что на сервере установлен правильный часовой пояс. Проверьте текущий часовой пояс:

```bash
timedatectl
```

Если часовой пояс не Europe/Sofia, установите его:

```bash
sudo timedatectl set-timezone Europe/Sofia
```

Проверьте, что часовой пояс установлен правильно:

```bash
date
```

## Шаг 10: Установка и настройка Cron для автоматического запуска

### Проверка и установка Cron

Сначала убедитесь, что cron установлен в системе:

```bash
# Проверьте, установлен ли cron
which crontab

# Если команда не найдена, установите cron (требуются права sudo)
sudo apt-get update
sudo apt-get install -y cron
```

Проверьте, что cron-сервис запущен:

```bash
sudo systemctl status cron
```

Если сервис не запущен, запустите его:

```bash
sudo systemctl start cron
sudo systemctl enable cron
```

### Настройка Cron-задачи

**Важно:** Настройку cron нужно выполнять от имени пользователя, который будет запускать скрипт (например, `bot-user`), а не от имени администратора.

Переключитесь на пользователя, который будет запускать скрипт:

```bash
# Если вы администратор, переключитесь на пользователя bot-user:
sudo su - bot-user

# Или если вы уже залогинены как bot-user, продолжайте
```

Откройте crontab для редактирования:

```bash
crontab -e
```

Если это первый раз, выберите редактор (рекомендуется `nano`).

Добавьте следующую строку в конец файла для запуска скрипта ежедневно в 9:00 по времени Софии:

```cron
0 9 * * * cd /home/alobg/alobg && /home/alobg/alobg/venv/bin/python main.py >> /home/alobg/alobg/logs/cron.log 2>&1
```

**Важно:** Замените `/home/alobg/alobg` на фактический путь к вашему проекту.

**Формат cron-задачи:**
- `0 9 * * *` - запуск в 9:00 каждый день
- `cd /path/to/project` - переход в директорию проекта
- `&&` - выполнение следующей команды только если предыдущая успешна
- `/path/to/venv/bin/python main.py` - запуск скрипта через Python из виртуального окружения
- `>> /path/to/logs/cron.log` - добавление вывода в лог-файл
- `2>&1` - перенаправление ошибок в тот же лог-файл

**Примеры других расписаний:**

- Каждый день в 9:30: `30 9 * * *`
- Каждый день в 8:00 и 20:00: `0 8,20 * * *`
- Каждый понедельник в 9:00: `0 9 * * 1`
- Каждый день в 9:00, кроме выходных: `0 9 * * 1-5`

Сохраните файл (в nano: `Ctrl+O`, затем `Enter`, затем `Ctrl+X`).

Проверьте, что задача добавлена:

```bash
crontab -l
```

## Шаг 11: Создание директории для логов

Убедитесь, что директория для логов существует:

```bash
mkdir -p ~/alobg/logs
```

## Шаг 12: Настройка прав доступа

Убедитесь, что у пользователя есть права на запись в директорию проекта:

```bash
chmod -R u+w ~/alobg
```

## Шаг 13: Проверка работы Cron

Проверьте, что cron-сервис запущен:

```bash
sudo systemctl status cron
```

Если сервис не запущен, запустите его:

```bash
sudo systemctl start cron
sudo systemctl enable cron
```

Для тестирования cron-задачи можно временно установить запуск через 2 минуты:

```bash
crontab -e
# Добавьте строку (замените на текущее время + 2 минуты):
# Например, если сейчас 14:30, используйте 32 14:
32 14 * * * cd /home/alobg/alobg && /home/alobg/alobg/venv/bin/python main.py >> /home/alobg/alobg/logs/cron.log 2>&1
```

Подождите 2 минуты и проверьте логи:

```bash
tail -f ~/alobg/logs/cron.log
tail -f ~/alobg/logs/alo_auto_bump.log
```

После проверки верните правильное время в crontab.

## Шаг 14: Мониторинг и логирование

### Просмотр логов Cron

Логи cron-запусков сохраняются в файл, указанный в crontab:

```bash
tail -f ~/alobg/logs/cron.log
```

### Просмотр логов приложения

Основные логи приложения:

```bash
tail -f ~/alobg/logs/alo_auto_bump.log
```

### Просмотр системных логов Cron

Системные логи cron:

```bash
sudo tail -f /var/log/syslog | grep CRON
```

## Устранение неполадок

### Проблема: Скрипт не запускается по расписанию

1. **Проверьте, что cron-сервис запущен:**
   ```bash
   sudo systemctl status cron
   ```

2. **Проверьте синтаксис crontab:**
   ```bash
   crontab -l
   ```

3. **Проверьте системные логи:**
   ```bash
   sudo grep CRON /var/log/syslog | tail -20
   ```

4. **Проверьте права доступа к файлам:**
   ```bash
   ls -la ~/alobg/main.py
   ls -la ~/alobg/.env
   ```

5. **Убедитесь, что используются абсолютные пути в crontab**

### Проблема: "ModuleNotFoundError"

Убедитесь, что в crontab используется Python из виртуального окружения:

```bash
# Проверьте путь к Python
which python
# Должен быть: /home/alobg/alobg/venv/bin/python

# В crontab используйте полный путь:
/home/alobg/alobg/venv/bin/python
```

### Проблема: "Permission denied"

Проверьте права доступа:

```bash
chmod +x ~/alobg/main.py
chmod 600 ~/alobg/.env
chmod -R u+w ~/alobg/logs
```

### Проблема: Неправильное время выполнения

1. **Проверьте часовой пояс:**
   ```bash
   timedatectl
   date
   ```

2. **Убедитесь, что cron использует правильный часовой пояс:**
   ```bash
   # Проверьте переменную TZ в crontab
   crontab -e
   # Добавьте в начало файла:
   TZ=Europe/Sofia
   ```

### Проблема: Playwright не может запустить браузер

**Ошибка: `libnspr4.so: cannot open shared object file: No such file or directory`**

Эта ошибка означает, что отсутствуют системные библиотеки, необходимые для запуска Chromium.

**Решение:**

1. **Если у вас есть права sudo:**

   **Рекомендуемый способ** - установка через apt-get:

   **Для Ubuntu 22.04 и ниже:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y libnspr4 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 libatspi2.0-0 libxshmfence1
   ```

   **Для Ubuntu 24.04 и выше (с пакетами t64):**
   ```bash
   sudo apt-get update
   sudo apt-get install -y libnspr4 libnss3 libatk1.0-0t64 libatk-bridge2.0-0t64 libcups2t64 libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2t64 libpango-1.0-0 libcairo2 libatspi2.0-0t64 libxshmfence1
   ```

   **Альтернативный способ** - через playwright (только если playwright установлен глобально или вы активировали виртуальное окружение):
   ```bash
   # Если playwright установлен глобально:
   sudo playwright install-deps chromium

   # Или если нужно использовать из виртуального окружения:
   cd /home/bot-user/alobg
   source venv/bin/activate
   sudo -E env "PATH=$PATH" playwright install-deps chromium
   ```

2. **Если у вас НЕТ прав sudo (ваша ситуация):**

   Вам нужно попросить администратора сервера установить недостающие библиотеки. Отправьте администратору следующую команду:

   **Для Ubuntu 22.04 и ниже:**
   ```bash
   sudo apt-get update && sudo apt-get install -y libnspr4 libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2 libpango-1.0-0 libcairo2 libatspi2.0-0 libxshmfence1
   ```

   **Для Ubuntu 24.04 и выше (с пакетами t64):**
   ```bash
   sudo apt-get update && sudo apt-get install -y libnspr4 libnss3 libatk1.0-0t64 libatk-bridge2.0-0t64 libcups2t64 libdrm2 libdbus-1-3 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2t64 libpango-1.0-0 libcairo2 libatspi2.0-0t64 libxshmfence1
   ```

   Или попросите выполнить:
   ```bash
   sudo playwright install-deps chromium
   ```

   **Минимальный набор библиотек** (если администратор хочет установить только самое необходимое):
   ```bash
   sudo apt-get install -y libnspr4 libnss3
   ```

3. **После установки библиотек администратором:**

   Проверьте, что браузер установлен:
   ```bash
   cd ~/alobg
   source venv/bin/activate
   playwright install chromium
   ```

   Попробуйте запустить скрипт:
   ```bash
   python main.py
   ```

4. **Проверка установленных библиотек:**

   Если у вас есть доступ к системе, можете проверить, какие библиотеки установлены:
   ```bash
   ldconfig -p | grep libnspr
   ldconfig -p | grep libnss
   ```

**Примечание:** Без установки этих системных библиотек Chromium не сможет запуститься. Это обязательное требование для работы Playwright.

### Проблема: Скрипт работает вручную, но не через cron

Cron использует минимальное окружение. Добавьте переменные окружения в crontab:

```bash
crontab -e
```

Добавьте в начало файла:

```cron
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
TZ=Europe/Sofia

# Ваша задача
0 9 * * * cd /home/alobg/alobg && /home/alobg/alobg/venv/bin/python main.py >> /home/alobg/alobg/logs/cron.log 2>&1
```

## Дополнительные настройки

### Настройка ротации логов

Для предотвращения переполнения диска логами можно настроить logrotate:

```bash
sudo nano /etc/logrotate.d/alobg
```

Добавьте:

```
/home/alobg/alobg/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 alobg alobg
}
```

### Настройка уведомлений об ошибках

Можно настроить отправку email при ошибках через cron. Добавьте в crontab:

```cron
MAILTO=your_email@example.com
```

Или используйте существующую интеграцию с Telegram для уведомлений об ошибках.

### Резервное копирование

Рекомендуется настроить резервное копирование файла `.env` и других важных данных:

```bash
# Создайте скрипт резервного копирования
nano ~/backup_alobg.sh
```

```bash
#!/bin/bash
BACKUP_DIR=~/backups
mkdir -p $BACKUP_DIR
tar -czf $BACKUP_DIR/alobg_backup_$(date +%Y%m%d_%H%M%S).tar.gz ~/alobg/.env ~/alobg/logs
# Удалите старые резервные копии (старше 30 дней)
find $BACKUP_DIR -name "alobg_backup_*.tar.gz" -mtime +30 -delete
```

Сделайте скрипт исполняемым:

```bash
chmod +x ~/backup_alobg.sh
```

Добавьте в crontab для ежедневного резервного копирования:

```cron
0 2 * * * /home/alobg/backup_alobg.sh
```

## Проверка работоспособности

После настройки проверьте:

1. ✅ Скрипт запускается вручную
2. ✅ Получен отчёт в Telegram
3. ✅ Cron-задача добавлена (`crontab -l`)
4. ✅ Часовой пояс установлен правильно (`date`)
5. ✅ Логи создаются корректно
6. ✅ Тестовый запуск через cron прошёл успешно

## Полезные команды

```bash
# Просмотр активных cron-задач
crontab -l

# Редактирование cron-задач
crontab -e

# Удаление всех cron-задач (осторожно!)
crontab -r

# Просмотр логов в реальном времени
tail -f ~/alobg/logs/alo_auto_bump.log

# Проверка статуса cron-сервиса
sudo systemctl status cron

# Перезапуск cron-сервиса
sudo systemctl restart cron
```

## Безопасность

1. **Храните `.env` файл в безопасности:**
   ```bash
   chmod 600 ~/alobg/.env
   ```

2. **Не коммитьте `.env` в Git:**
   Убедитесь, что `.env` находится в `.gitignore`

3. **Используйте отдельного пользователя** для запуска скрипта (не root)

4. **Регулярно обновляйте зависимости:**
   ```bash
   cd ~/alobg
   source venv/bin/activate
   pip install --upgrade -r requirements.txt
   ```

## Поддержка

При возникновении проблем проверьте:
- Логи приложения: `~/alobg/logs/alo_auto_bump.log`
- Логи cron: `~/alobg/logs/cron.log`
- Системные логи: `sudo grep CRON /var/log/syslog`
