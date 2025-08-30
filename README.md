## QuizMaster — Telegram Quiz Bot (aiogram 3 + FastAPI + PostgreSQL)

### Кратко
Бот для прохождения тестов с вариантами ответов и комментариями. Включает:
- Telegram-бот на aiogram 3 (FSM с сохранением состояния)
- REST API на FastAPI (админ и публичные роуты)
- PostgreSQL для доменных данных и FSM состояний

### Стек
- aiogram 3, FastAPI, Uvicorn
- SQLAlchemy 2, PostgreSQL
- Pydantic 2, python-dotenv, requests, aiohttp

### Архитектура
- `app/bot`: Telegram-бот, обращается к API по HTTP
- `app/api`: FastAPI-приложение (`/public` и `/admin`)
- `app/core`: модели, сервисы, конфиг, доступ к БД
- Хранилище: реализовано на PostgreSQL (см. `app/core/db_storage.py`, `app/core/database.py`). FSM бота хранится в таблице `user_states`.

### Структура проекта (основное)
- `app/api/main.py` — инициализация FastAPI, CORS, роуты
- `app/api/routers/public.py` — публичные эндпоинты для бота
- `app/api/routers/admin.py` — эндпоинты для импорта/статистики
- `app/bot/bot.py`, `app/bot/handlers.py` — бот и обработчики
- `app/core/database.py` — SQLAlchemy-модели и engine
- `app/core/db_storage.py` — реализация доступа к PostgreSQL
- `main.py` — параллельный запуск API и бота

Дополнительно:
- `docs/architecture.md` — детализация архитектуры
- `docs/setup_local_db.md` — настройка локальной БД
- `docs/cursor_rules.md` — правила для Cursor/модели
- `scripts/import_from_prod_dump.py` — импорт из prod_dump JSON напрямую в БД

### Быстрый старт (локально)
1) Требования: Docker, Python 3.11+

2) Среда окружения: создайте файл `.env` в корне проекта (пример в `.env.example`).
Минимум переменных:
```
BOT_TOKEN=ВАШ_ТОКЕН_БОТА
API_HOST=0.0.0.0
API_PORT=5000
ADMIN_API_KEY=admin_secret_key_123
DATABASE_URL=postgresql://quiz:quizpass@localhost:5435/quizmaster
```

3) Поднять изолированный PostgreSQL (порт 5435, чтобы не конфликтовать с существующими):
```
docker run --name quizmaster-postgres -e POSTGRES_USER=quiz -e POSTGRES_PASSWORD=quizpass -e POSTGRES_DB=quizmaster -p 5435:5432 -d postgres:16
```

4) Установить минимальные зависимости для БД-инициализации:
```
python3 -m pip install -U pip
python3 -m pip install "SQLAlchemy>=2.0.43" "psycopg2-binary>=2.9.10" "python-dotenv>=1.1.1"
```

5) Инициализировать таблицы:
```
python3 init_db.py
```

6) Импортировать вопросы из prod_dump (файлы теперь в папке data/):
```
python3 scripts/import_from_prod_dump.py --file data/prod_transfer_20250825_191222.json
```

7) Запуск
- Только API: `python3 run_api.py`
- Только бот: `python3 run_bot.py`
- Оба процесса: `python3 main.py`

API по умолчанию на `http://localhost:5000` (`/docs` для Swagger UI).

### Режим вебхука (для прод):
- Установите переменные окружения:
```
BOT_WEBHOOK_ENABLED=true
WEBHOOK_URL=https://<ваш-домен>/webhook
WEBHOOK_PATH_PREFIX=/webhook
```
- Настройте у Telegram: `https://api.telegram.org/bot<token>/setWebhook?url=<WEBHOOK_URL>`
- В dev по умолчанию вебхук выключен (используется polling).

### Особенности и инварианты
- Ровно один правильный ответ на вопрос (валидация при импорте/логике)
- FSM состояния сохраняются в таблицу `user_states`
- Бот взаимодействует с API только через HTTP

### Безопасность админ-роутов
Планируется защита по ключу `X-API-Key` (см. `app/api/deps.py`). Подключение зависимости в роутеры может быть включено в отдельной задаче. На локальном окружении используйте `ADMIN_API_KEY` из `.env`.

### Правила для Cursor/модели
См. `docs/cursor_rules.md`. Коротко:
- Не придумывать новые сущности/поля/поведение без задачи
- Конфигурация только через `.env`/переменные окружения
- Любые изменения — минимально инвазивные: не ломать существующие импорты/роуты

### Траблшутинг
- Если порт 5432 занят — мы используем 5435 для локального контейнера
- Если нет зависимостей — установите минимальный набор (см. шаг 4)
- Проверка БД: `python3 init_db.py` выведет список созданных таблиц


