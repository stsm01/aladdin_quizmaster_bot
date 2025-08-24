# README — Telegram Quiz Bot (aiogram + FastAPI + Postgres) для Replit

Этот файл — полные инструкции и стартовый шаблон. С его помощью вы быстро поднимете MVP‑бота для проверки знаний аккаунт‑менеджеров.

## 1) Что это и как работает

- Telegram‑бот (aiogram 3) задаёт вопросы с вариантами.
- После каждого ответа показывает «верно/неверно» и комментарий.
- В конце выводит процент правильных ответов.
- Все события пишутся в PostgreSQL. Поддерживаются повторные прохождения (сессии).
- Вопросы загружаются через админ‑API одним JSON (см. раздел **Тестовый JSON**).

## 2) Стек и требования

- Python 3.11+
- aiogram 3, FastAPI, SQLAlchemy 2, asyncpg, Alembic
- PostgreSQL (Neon/другой managed Postgres). Рекомендуется Neon (бесплатный план).

## 3) Переменные окружения (Replit → Secrets)

Создайте в Replit Secrets:

```
BOT_TOKEN=<токен_бота_из_@BotFather>
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>/<db>?sslmode=require
API_HOST=0.0.0.0
API_PORT=8000
ADMIN_API_KEY=<длинный_рандомный_ключ>
```

## 4) Установка зависимостей

Создайте `requirements.txt` со следующим содержимым:

```
aiogram==3.*
fastapi==0.111.*
uvicorn[standard]==0.30.*
pydantic==2.*
SQLAlchemy==2.*
asyncpg==0.29.*
alembic==1.*
python-dotenv==1.*
structlog==24.*
```

В Replit зависимости подтянутся автоматически, либо выполните в Shell:

```
pip install -r requirements.txt
```

## 5) Структура проекта

```
/app
  /bot
    bot.py                 # вход для aiogram
    handlers.py            # хендлеры и FSM
    keyboards.py           # inline-клавиатуры
    texts.py               # русские тексты сообщений/кнопок
  /api
    main.py                # вход для FastAPI
    deps.py                # зависимости (БД, авторизация)
    routers/
      admin.py             # импорт/управление вопросами (X-API-Key)
      public.py            # публичные ручки (сессии, вопросы, статистика)
  /core
    config.py              # загрузка env
    db.py                  # сессия БД
    models.py              # SQLAlchemy модели
    schemas.py             # Pydantic модели
    services.py            # бизнес-логика
  /migrations
    env.py / versions/...  # Alembic
alembic.ini
requirements.txt
README.md
```

> Совет: можно начать с пустых файлов из шаблонов ниже, а потом постепенно дополнять.

## 6) Модели БД (первая миграция)

**ER:** `users` (1) —< `quiz_sessions` (N) —< `user_answers` (N); `questions` (1) —< `answer_options` (N) —< `user_answers` (N)

SQL (для Alembic миграции):

```sql
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  telegram_id BIGINT NOT NULL UNIQUE,
  first_name TEXT NOT NULL,
  last_name  TEXT NOT NULL,
  registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE quiz_sessions (
  id UUID PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  finished_at TIMESTAMPTZ,
  question_order INT[] NOT NULL,
  correct_count INT NOT NULL DEFAULT 0,
  total_count   INT NOT NULL DEFAULT 0
);

CREATE TABLE questions (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  text  TEXT NOT NULL
);

CREATE TABLE answer_options (
  id TEXT PRIMARY KEY,
  question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  text TEXT NOT NULL,
  is_correct BOOLEAN NOT NULL,
  comment TEXT NOT NULL
);

CREATE INDEX ix_answer_options_question_id ON answer_options(question_id);

CREATE TABLE user_answers (
  id BIGSERIAL PRIMARY KEY,
  session_id UUID NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
  user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  question_id TEXT NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
  chosen_option_id TEXT NOT NULL REFERENCES answer_options(id),
  is_correct BOOLEAN NOT NULL,
  answered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE(session_id, question_id)
);
```

## 7) Минимальные каркасы файлов

Создайте файлы с этим содержимым и дорабатывайте по мере необходимости.

### `/app/core/config.py`

```python
from pydantic import BaseModel
from dotenv import load_dotenv
import os
load_dotenv()

class Settings(BaseModel):
    bot_token: str = os.getenv("BOT_TOKEN", "")
    database_url: str = os.getenv("DATABASE_URL", "")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    admin_api_key: str = os.getenv("ADMIN_API_KEY", "")

settings = Settings()
```

### `/app/core/db.py`

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

engine = create_async_engine(settings.database_url, echo=False, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_session() -> AsyncSession:
    async with SessionLocal() as s:
        yield s
```

### `/app/api/deps.py`

```python
from fastapi import Header, HTTPException, status
from app.core.config import settings

def admin_auth(x_api_key: str = Header(..., alias="X-API-Key")):
    if x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
```

### `/app/api/main.py`

```python
from fastapi import FastAPI
from app.api.routers import admin, public

app = FastAPI(title="AM Quiz API", version="0.1.0")
app.include_router(admin.router, prefix="/admin", tags=["admin"])
app.include_router(public.router, prefix="/public", tags=["public"])
```

### `/app/bot/bot.py`

```python
import asyncio
from aiogram import Bot, Dispatcher
from app.core.config import settings
from app.bot.handlers import register_handlers

async def main():
    bot = Bot(settings.bot_token, parse_mode="HTML")
    dp = Dispatcher()
    register_handlers(dp)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

### `/app/bot/handlers.py`

```python
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

router = Router()

def register_handlers(dp):
    dp.include_router(router)

@router.message(CommandStart())
async def on_start(msg: Message):
    # TODO: создать/проверить пользователя через API, спросить ФИО, предложить начать тест
    await msg.answer("Привет! Я помогу проверить знания. Нажмите: /start ещё раз, если что-то пошло не так.")

@router.message(F.text.regexp(r"^\S+\s+\S+"))
async def on_fullname(msg: Message):
    # TODO: сохранить имя/фамилию через API
    await msg.answer("Спасибо! Готовы начать тест? Нажмите кнопку или команду.")

@router.callback_query(F.data == "start_quiz")
async def start_quiz(cb: CallbackQuery):
    # TODO: POST /public/sessions/start и отправить первый вопрос
    await cb.answer()
    await cb.message.answer("Начинаем! (Заглушка)")

@router.callback_query(F.data.startswith("opt:"))
async def answer(cb: CallbackQuery):
    # TODO: разобрать callback data и отправить ответ в API, показать комментарий и прогресс
    await cb.answer()
```

> В `routers/admin.py`, `routers/public.py`, `core/models.py`, `core/services.py` предусмотрите реализацию по контрактам из раздела 9.

## 8) Миграции Alembic

Инициализация (если нужно):

```
alembic init migrations
```

Настройте `alembic.ini` → `sqlalchemy.url = ${DATABASE_URL}` (или прокидывайте через env). Создайте ревизию и добавьте SQL из раздела 6.

```
alembic revision -m "init"
# вставьте SQL в upgrade()
alembic upgrade head
```

## 9) Контракты API

Аутентификация админ‑ручек: заголовок `X-API-Key: <ADMIN_API_KEY>`.

1. `POST /admin/questions/import` — импорт массива вопросов в формате ниже. Валидация: на каждый вопрос ровно один `is_correct=true`.

2. `GET /public/users/{telegram_id}/stats` — сводка по пользователю:

```json
{
  "telegram_id": 123,
  "full_name": "Имя Фамилия",
  "registrations": "2025-08-24T10:00:00Z",
  "attempts": 3,
  "last_score_percent": 82,
  "best_score_percent": 91
}
```

3. `POST /public/sessions/start` — начало сессии:

```json
{ "telegram_id": 123, "shuffle": true }
```

Ответ:

```json
{ "session_id": "<uuid>", "total": 18 }
```

4. `GET /public/sessions/{session_id}/next` — следующий вопрос (или 204 если закончились).

5. `POST /public/sessions/{session_id}/answer` — принять ответ и вернуть `{ is_correct, comment, progress }`.

6. `POST /public/sessions/{session_id}/finish` — завершить и вернуть итоговый процент.

## 10) Запуск на Replit

1. Создайте проект, добавьте файлы по структуре выше.
2. Добавьте Secrets (см. раздел 3).
3. Примените миграции Alembic к вашей базе (Neon) — через Shell.
4. Запустите API:

```
uvicorn app.api.main:app --host $API_HOST --port $API_PORT
```

5. В новой Shell‑вкладке запустите бота:

```
python -m app.bot.bot
```

> В Replit можно держать два процесса параллельно в разных Shell‑вкладках.

## 11) Импорт тестовых вопросов (curl)

После запуска API выполните в своей машине/в Replit Shell:

```
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $ADMIN_API_KEY" \
  --data @questions.json \
  "http://localhost:8000/admin/questions/import"
```

Либо вместо `--data @questions.json` вставьте JSON из следующего раздела.

## 12) Тестовый JSON для загрузки в БД

Сохраните в файл `questions.json` и импортируйте через `/admin/questions/import`.

```json
[
{
"ID вопроса": "Q001",
"Формулировка вопроса": "Включение саморегистрации",
"Текст вопроса": "Где включается возможность самостоятельной регистрации сотрудников для конкретной организации?",
"Ответы": [
{
"ID ответа": "Q001A1",
"Текст ответа": "В админке, во вкладке «Прочие», с помощью галочки «Разрешить самостоятельную регистрацию».",
"Правильный-неправильный ответ": true,
"Комментарий к ответу": "Именно так включается саморегистрация; без этого на логин-экране не появится вкладка «Регистрация»."
},
{
"ID ответа": "Q001A2",
"Текст ответа": "В карточке провайдера, раздел «Настройки чеков».",
"Правильный-неправильный ответ": false,
"Комментарий к ответу": "Настройки чеков относятся к НДС и чекам провайдера, а не к саморегистрации сотрудников."
},
{
"ID ответа": "Q001A3",
"Текст ответа": "В пользовательском кабинете сотрудника, раздел «Профиль».",
"Правильный-неправильный ответ": false,
"Комментарий к ответу": "Саморегистрация настраивается на стороне организации в админке, а не в личном кабинете сотрудника."
}
]
},
{
"ID вопроса": "Q002",
"Формулировка вопроса": "Код приглашения",
"Текст вопроса": "Как устроен код, необходимый для саморегистрации, и можно ли передать его через ссылку/QR?",
"Ответы": [
{
"ID ответа": "Q002A1",
"Текст ответа": "Код состоит из трёх латинских букв и трёх цифр; его можно вшить в ссылку или QR-код.",
"Правильный-неправильный ответ": true,
"Комментарий к ответу": "Система генерирует код формата LLLDDD, и дл
```
