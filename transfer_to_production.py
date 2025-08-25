#!/usr/bin/env python3
"""
Перенос данных из development базы в production базу
"""

import os
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Настройки баз данных
DEV_DATABASE_URL = os.getenv("DATABASE_URL")  # Development база
PROD_DATABASE_URL = "postgresql://neondb_owner:npg_9BH3JEMRwQna@ep-bitter-lake-a69kivks.us-west-2.aws.neon.tech/neondb?sslmode=require"  # Production база

def connect_to_db(database_url, db_name):
    """Подключение к базе данных"""
    try:
        engine = create_engine(database_url, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        print(f"✅ Подключение к {db_name} базе успешно")
        return session, engine
    except Exception as e:
        print(f"❌ Ошибка подключения к {db_name} базе: {e}")
        return None, None

def export_from_dev():
    """Экспорт данных из dev базы"""
    print("🔄 Экспортируем данные из development базы...")
    
    if not DEV_DATABASE_URL:
        print("❌ DATABASE_URL не найден!")
        return None
        
    dev_session, dev_engine = connect_to_db(DEV_DATABASE_URL, "development")
    if not dev_session:
        return None
    
    try:
        # Экспорт тестов
        tests_result = dev_session.execute(text("""
            SELECT id, name, description, created_at 
            FROM tests 
            ORDER BY created_at
        """))
        tests = [dict(row._mapping) for row in tests_result]
        print(f"   📋 Найдено {len(tests)} тестов")
        
        # Экспорт вопросов
        questions_result = dev_session.execute(text("""
            SELECT id, test_id, title, text, created_at 
            FROM questions 
            ORDER BY created_at
        """))
        questions = [dict(row._mapping) for row in questions_result]
        print(f"   ❓ Найдено {len(questions)} вопросов")
        
        # Экспорт вариантов ответов
        options_result = dev_session.execute(text("""
            SELECT id, question_id, text, is_correct, comment 
            FROM answer_options 
            ORDER BY id
        """))
        answer_options = [dict(row._mapping) for row in options_result]
        print(f"   🔘 Найдено {len(answer_options)} вариантов ответов")
        
        data = {
            "tests": tests,
            "questions": questions,
            "answer_options": answer_options,
            "export_time": datetime.now().isoformat()
        }
        
        return data
        
    except Exception as e:
        print(f"❌ Ошибка экспорта: {e}")
        return None
    finally:
        dev_session.close()
        dev_engine.dispose()

def import_to_production(data):
    """Импорт данных в production базу"""
    print("🚀 Импортируем данные в production базу...")
    
    if not PROD_DATABASE_URL:
        print("❌ PROD_DATABASE_URL не найден! Используем ту же базу что и dev.")
        prod_url = DEV_DATABASE_URL
    else:
        prod_url = PROD_DATABASE_URL
        
    prod_session, prod_engine = connect_to_db(prod_url, "production")
    if not prod_session:
        return False
    
    try:
        # Создаем таблицы если их нет
        print("🏗️  Создаем структуру таблиц...")
        
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
                test_id VARCHAR NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
                title VARCHAR NOT NULL,
                text TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """))
        
        prod_session.execute(text("""
            CREATE TABLE IF NOT EXISTS answer_options (
                id VARCHAR PRIMARY KEY,
                question_id VARCHAR NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
                text TEXT NOT NULL,
                is_correct BOOLEAN NOT NULL,
                comment TEXT NOT NULL
            )
        """))
        
        prod_session.commit()
        print("   ✅ Структура таблиц готова")
        
        # Очищаем старые данные
        print("🗑️  Очищаем старые данные...")
        prod_session.execute(text("DELETE FROM answer_options"))
        prod_session.execute(text("DELETE FROM questions"))
        prod_session.execute(text("DELETE FROM tests"))
        prod_session.commit()
        
        # Импортируем новые данные
        print("📋 Импортируем тесты...")
        for test in data["tests"]:
            prod_session.execute(text("""
                INSERT INTO tests (id, name, description, created_at) 
                VALUES (:id, :name, :description, :created_at)
            """), test)
        print(f"   ✅ Импортировано {len(data['tests'])} тестов")
        
        print("❓ Импортируем вопросы...")
        for question in data["questions"]:
            prod_session.execute(text("""
                INSERT INTO questions (id, test_id, title, text, created_at) 
                VALUES (:id, :test_id, :title, :text, :created_at)
            """), question)
        print(f"   ✅ Импортировано {len(data['questions'])} вопросов")
        
        print("🔘 Импортируем варианты ответов...")
        for option in data["answer_options"]:
            prod_session.execute(text("""
                INSERT INTO answer_options (id, question_id, text, is_correct, comment) 
                VALUES (:id, :question_id, :text, :is_correct, :comment)
            """), option)
        print(f"   ✅ Импортировано {len(data['answer_options'])} вариантов")
        
        prod_session.commit()
        
        # Проверяем результат
        test_count = prod_session.execute(text("SELECT COUNT(*) FROM tests")).scalar()
        question_count = prod_session.execute(text("SELECT COUNT(*) FROM questions")).scalar()
        option_count = prod_session.execute(text("SELECT COUNT(*) FROM answer_options")).scalar()
        
        print("✅ Импорт завершен успешно!")
        print(f"📊 В production базе:")
        print(f"   📋 Тестов: {test_count}")
        print(f"   ❓ Вопросов: {question_count}")
        print(f"   🔘 Вариантов: {option_count}")
        
        return True
        
    except Exception as e:
        prod_session.rollback()
        print(f"❌ Ошибка импорта: {e}")
        return False
    finally:
        prod_session.close()
        prod_engine.dispose()

def main():
    """Основная функция"""
    print("🚀 Перенос данных из DEV в PRODUCTION")
    print("=" * 50)
    
    print(f"🔗 DEV база: {DEV_DATABASE_URL.split('@')[1] if DEV_DATABASE_URL and '@' in DEV_DATABASE_URL else 'не найдена'}")
    print(f"🔗 PROD база: {PROD_DATABASE_URL.split('@')[1] if PROD_DATABASE_URL and '@' in PROD_DATABASE_URL else 'не указана (используем DEV)'}")
    print()
    
    # Экспорт из dev
    data = export_from_dev()
    if not data:
        print("❌ Не удалось экспортировать данные из dev базы")
        return
    
    # Сохранение бэкапа
    backup_file = f"prod_transfer_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"💾 Бэкап сохранен: {backup_file}")
    
    # Импорт в production
    success = import_to_production(data)
    
    if success:
        print("=" * 50)
        print("🎉 Данные успешно перенесены в production базу!")
        
        # Показываем перенесенные тесты
        if data["tests"]:
            print("\n📋 Перенесенные тесты:")
            for test in data["tests"]:
                questions_count = len([q for q in data["questions"] if q["test_id"] == test["id"]])
                print(f"   • {test['name']} ({questions_count} вопросов)")
    else:
        print("=" * 50)
        print("❌ Ошибка при переносе данных")

if __name__ == "__main__":
    main()