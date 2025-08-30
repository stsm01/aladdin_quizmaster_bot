### Архитектура QuizMaster

Компоненты:
- Бот (`app/bot`): aiogram 3, FSM, диалоги и клавиатуры
- API (`app/api`): FastAPI, разделение `/public` и `/admin`
- Ядро (`app/core`): конфиг, модели (Pydantic), сервисы, доступ к БД
- Хранилище: PostgreSQL (SQLAlchemy 2)

Данные:
- Доменные таблицы: `tests`, `questions`, `answer_options`, `users`, `quiz_sessions`, `user_answers`
- FSM: `user_states` для хранения состояний и данных FSM бота

Потоки:
- Бот -> API: HTTP-запросы к публичным ручкам
- Админ импорт: `/admin/questions/import` (или загрузка напрямую в БД скриптом)

Запуск:
- `main.py` поднимает API и Бот параллельно
- Можно запускать по отдельности (`run_api.py`, `run_bot.py`)

Конфигурация:
- `.env` (см. `.env.example`), переменные читаются в `app/core/config.py`


