# Чат-бот Telegram на базе Yandex Assistant для Bitrix24

Бот отвечает на вопросы разработчиков по API Bitrix24.

## Установка
1. Клонируйте репозиторий.
2. `pip install -r requirements.txt`
3. Установите PostgreSQL, создайте БД `bitrix_bot_db`.
4. Создайте `.env` (см. ниже).
5. Запустите `python setup_index.py`, получите `YA_ASSISTANT_ID` и впишите в `.env`.
6. Запустите `python bot.py`.

## Описание .env файла

| Переменная | Описание | Пример |
|------------|----------|--------|
| `TELEGRAM_BOT_TOKEN` | Токен Telegram-бота | `1234567890:AAHSD...` |
| `YA_FOLDER_ID` | ID каталога Yandex Cloud | `b1g2v4c4...` |
| `YA_API_KEY` | API-ключ сервисного аккаунта | `AQVN...` |
| `YA_ASSISTANT_ID` | ID ассистента | `fvt...` |
| `DATABASE_URL` | Строка подключения к БД | `postgresql://postgres:pass@localhost:5432/bitrix_bot_db` |