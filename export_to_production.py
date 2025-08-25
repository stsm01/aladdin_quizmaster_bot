#!/usr/bin/env python3
"""
Скрипт для экспорта тестов из развертки в продовую базу данных
Экспортирует: тесты, вопросы, варианты ответов
"""

import json
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Конфигурация баз данных
DEV_DATABASE_URL = os.getenv("DATABASE_URL")
PROD_DATABASE_URL = os.getenv("PROD_DATABASE_URL", DEV_DATABASE_URL)  # Используем ту же БД если продовая не указана

def create_db_session(database_url):
    """Создать сессию базы данных"""
    engine = create_engine(database_url, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal(), engine

def export_tests_data():
    """Экспорт всех данных тестов"""
    print("🔄 Экспортируем данные тестов...")
    
    dev_session, dev_engine = create_db_session(DEV_DATABASE_URL)
    
    try:
        # Экспорт тестов
        tests_result = dev_session.execute(text("""
            SELECT id, name, description, created_at 
            FROM tests 
            ORDER BY created_at
        """))
        tests = [dict(row._mapping) for row in tests_result]
        print(f"✅ Найдено {len(tests)} тестов")
        
        all_data = {"tests": tests, "questions": [], "answer_options": []}
        
        # Для каждого теста экспортируем вопросы и ответы
        for test in tests:
            test_id = test['id']
            print(f"📝 Экспортируем вопросы для теста '{test['name']}'...")
            
            # Экспорт вопросов
            questions_result = dev_session.execute(text("""
                SELECT id, test_id, title, text, created_at 
                FROM questions 
                WHERE test_id = :test_id 
                ORDER BY created_at
            """), {"test_id": test_id})
            
            questions = [dict(row._mapping) for row in questions_result]
            all_data["questions"].extend(questions)
            print(f"   ✅ {len(questions)} вопросов")
            
            # Экспорт вариантов ответов для всех вопросов теста
            for question in questions:
                question_id = question['id']
                
                options_result = dev_session.execute(text("""
                    SELECT id, question_id, text, is_correct, comment 
                    FROM answer_options 
                    WHERE question_id = :question_id 
                    ORDER BY id
                """), {"question_id": question_id})
                
                options = [dict(row._mapping) for row in options_result]
                all_data["answer_options"].extend(options)
        
        print(f"✅ Всего экспортировано:")
        print(f"   📋 Тестов: {len(all_data['tests'])}")
        print(f"   ❓ Вопросов: {len(all_data['questions'])}")
        print(f"   🔘 Вариантов ответов: {len(all_data['answer_options'])}")
        
        return all_data
        
    finally:
        dev_session.close()
        dev_engine.dispose()

def import_to_production(data):
    """Импорт данных в продовую базу"""
    print("🚀 Импортируем данные в продовую базу...")
    
    prod_session, prod_engine = create_db_session(PROD_DATABASE_URL)
    
    try:
        # Проверка существования таблиц
        print("🔍 Проверяем структуру продовой базы...")
        
        # Создаем таблицы если их нет
        prod_session.execute(text("""
            CREATE TABLE IF NOT EXISTS tests (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                description TEXT DEFAULT '',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))
        
        prod_session.execute(text("""
            CREATE TABLE IF NOT EXISTS questions (
                id VARCHAR PRIMARY KEY,
                test_id VARCHAR NOT NULL REFERENCES tests(id),
                title VARCHAR NOT NULL,
                text TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))
        
        prod_session.execute(text("""
            CREATE TABLE IF NOT EXISTS answer_options (
                id VARCHAR PRIMARY KEY,
                question_id VARCHAR NOT NULL REFERENCES questions(id),
                text TEXT NOT NULL,
                is_correct BOOLEAN NOT NULL,
                comment TEXT NOT NULL
            )
        """))
        
        prod_session.commit()
        print("✅ Структура таблиц готова")
        
        # Импорт тестов
        print("📋 Импортируем тесты...")
        for test in data["tests"]:
            # Проверяем существует ли тест
            existing = prod_session.execute(text(
                "SELECT id FROM tests WHERE id = :id"
            ), {"id": test["id"]}).first()
            
            if not existing:
                prod_session.execute(text("""
                    INSERT INTO tests (id, name, description, created_at) 
                    VALUES (:id, :name, :description, :created_at)
                """), {
                    "id": test["id"],
                    "name": test["name"], 
                    "description": test["description"],
                    "created_at": test["created_at"]
                })
                print(f"   ➕ Добавлен тест: {test['name']}")
            else:
                print(f"   ⏭️  Тест уже существует: {test['name']}")
        
        # Импорт вопросов
        print("❓ Импортируем вопросы...")
        for question in data["questions"]:
            existing = prod_session.execute(text(
                "SELECT id FROM questions WHERE id = :id"
            ), {"id": question["id"]}).first()
            
            if not existing:
                prod_session.execute(text("""
                    INSERT INTO questions (id, test_id, title, text, created_at) 
                    VALUES (:id, :test_id, :title, :text, :created_at)
                """), {
                    "id": question["id"],
                    "test_id": question["test_id"],
                    "title": question["title"],
                    "text": question["text"],
                    "created_at": question["created_at"]
                })
        
        print(f"   ✅ Импортировано {len(data['questions'])} вопросов")
        
        # Импорт вариантов ответов
        print("🔘 Импортируем варианты ответов...")
        for option in data["answer_options"]:
            existing = prod_session.execute(text(
                "SELECT id FROM answer_options WHERE id = :id"
            ), {"id": option["id"]}).first()
            
            if not existing:
                prod_session.execute(text("""
                    INSERT INTO answer_options (id, question_id, text, is_correct, comment) 
                    VALUES (:id, :question_id, :text, :is_correct, :comment)
                """), {
                    "id": option["id"],
                    "question_id": option["question_id"],
                    "text": option["text"],
                    "is_correct": option["is_correct"],
                    "comment": option["comment"]
                })
        
        print(f"   ✅ Импортировано {len(data['answer_options'])} вариантов ответов")
        
        prod_session.commit()
        print("✅ Все данные успешно импортированы в продовую базу!")
        
        # Проверка результата
        test_count = prod_session.execute(text("SELECT COUNT(*) FROM tests")).scalar()
        question_count = prod_session.execute(text("SELECT COUNT(*) FROM questions")).scalar()
        option_count = prod_session.execute(text("SELECT COUNT(*) FROM answer_options")).scalar()
        
        print(f"📊 Итого в продовой базе:")
        print(f"   📋 Тестов: {test_count}")
        print(f"   ❓ Вопросов: {question_count}")
        print(f"   🔘 Вариантов ответов: {option_count}")
        
    except Exception as e:
        prod_session.rollback()
        print(f"❌ Ошибка импорта: {e}")
        raise
    finally:
        prod_session.close()
        prod_engine.dispose()

def main():
    """Основная функция"""
    print("🚀 Запуск экспорта тестов в продовую базу данных")
    print("=" * 50)
    
    # Экспорт из развертки
    data = export_tests_data()
    
    # Сохранение в файл для бэкапа
    backup_file = f"tests_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"💾 Бэкап сохранен в {backup_file}")
    
    # Импорт в продовую базу
    import_to_production(data)
    
    print("=" * 50)
    print("🎉 Экспорт завершен успешно!")

if __name__ == "__main__":
    main()