#!/usr/bin/env python3
"""
Импорт тестов, вопросов и ответов напрямую в PostgreSQL из prod_transfer_*.json

Использует SQLAlchemy-модели из app/core/database.py и DATABASE_URL из .env.
"""

import argparse
import json
import os
from typing import Any, Dict, List

from dotenv import load_dotenv

# Подтягиваем окружение
load_dotenv()

# Импортируем модели и сессию
from app.core.database import (
    SessionLocal,
    Base,
    engine,
    Test as DBTest,
    Question as DBQuestion,
    AnswerOption as DBAnswerOption,
)

def ensure_tables() -> None:
    Base.metadata.create_all(bind=engine)

def import_from_dump(file_path: str) -> None:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tests: List[Dict[str, Any]] = data.get("tests", [])
    questions: List[Dict[str, Any]] = data.get("questions", [])
    answer_options: List[Dict[str, Any]] = data.get("answer_options", [])

    db = SessionLocal()
    try:
        # Импорт тестов
        for t in tests:
            exists = db.query(DBTest).filter(DBTest.id == t["id"]).first()
            if not exists:
                db.add(DBTest(
                    id=t["id"],
                    name=t["name"],
                    description=t.get("description", ""),
                ))

        db.commit()

        # Импорт вопросов
        for q in questions:
            exists = db.query(DBQuestion).filter(DBQuestion.id == q["id"]).first()
            if not exists:
                db.add(DBQuestion(
                    id=q["id"],
                    test_id=q["test_id"],
                    title=q["title"],
                    text=q["text"],
                ))

        db.commit()

        # Импорт ответов
        for a in answer_options:
            exists = db.query(DBAnswerOption).filter(DBAnswerOption.id == a["id"]).first()
            if not exists:
                db.add(DBAnswerOption(
                    id=a["id"],
                    question_id=a["question_id"],
                    text=a["text"],
                    is_correct=bool(a["is_correct"]),
                    comment=a.get("comment", ""),
                ))

        db.commit()
        print("✅ Импорт завершён успешно")
    finally:
        db.close()

def main() -> None:
    parser = argparse.ArgumentParser(description="Импорт из prod_transfer_*.json в PostgreSQL")
    parser.add_argument("--file", required=True, help="Путь к JSON дампу (например, data/prod_transfer_*.json)")
    args = parser.parse_args()

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL не задан. Создайте .env и укажите строку подключения.")

    print(f"📦 Файл: {args.file}")
    print(f"🗄️  DATABASE_URL: {database_url}")

    ensure_tables()
    import_from_dump(args.file)

if __name__ == "__main__":
    main()


