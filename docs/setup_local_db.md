### Локальная БД (изолированная)

Чтобы не конфликтовать с уже установленными PostgreSQL на машине, используем Docker-контейнер на порту 5435.

1) Запуск контейнера:
```
docker run --name quizmaster-postgres -e POSTGRES_USER=quiz -e POSTGRES_PASSWORD=quizpass -e POSTGRES_DB=quizmaster -p 5435:5432 -d postgres:16
```

2) Переменные окружения (`.env`):
```
DATABASE_URL=postgresql://quiz:quizpass@localhost:5435/quizmaster
```

3) Инициализация таблиц:
```
python3 init_db.py
```

4) Импорт вопросов из prod_dump:
```
python3 scripts/import_from_prod_dump.py --file prod_transfer_20250825_191222.json
```


