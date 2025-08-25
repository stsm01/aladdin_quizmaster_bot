#!/usr/bin/env python3
"""
Простая проверка состояния тестов в базе данных
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def check_tests():
    """Проверить состояние тестов в базе"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        print("🔍 Проверяем продовую базу данных...")
        print(f"🔗 Database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'local'}")
        print()
        
        # Проверяем существование таблиц
        tables_result = session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        tables = [row[0] for row in tables_result]
        print(f"📋 Таблицы в базе: {', '.join(tables)}")
        
        if 'tests' not in tables:
            print("❌ Таблица 'tests' не найдена!")
            return
            
        # Считаем записи
        test_count = session.execute(text("SELECT COUNT(*) FROM tests")).scalar()
        question_count = session.execute(text("SELECT COUNT(*) FROM questions")).scalar() if 'questions' in tables else 0
        option_count = session.execute(text("SELECT COUNT(*) FROM answer_options")).scalar() if 'answer_options' in tables else 0
        
        print()
        print("📊 Состояние данных:")
        print(f"   📋 Тестов: {test_count}")
        print(f"   ❓ Вопросов: {question_count}")
        print(f"   🔘 Вариантов ответов: {option_count}")
        
        if test_count > 0:
            print()
            print("📝 Существующие тесты:")
            tests_result = session.execute(text("""
                SELECT t.name, t.description, COUNT(q.id) as questions_count 
                FROM tests t 
                LEFT JOIN questions q ON t.id = q.test_id 
                GROUP BY t.id, t.name, t.description 
                ORDER BY t.created_at
            """))
            
            for test in tests_result:
                print(f"   📋 {test[0]}")
                print(f"      📄 {test[1]}")
                print(f"      ❓ Вопросов: {test[2]}")
                print()
                
        else:
            print()
            print("⚠️  ВНИМАНИЕ: Тесты не найдены в базе данных!")
            print("💡 Если после деплоя тесты пропали, используйте:")
            print("   python export_to_production.py")
        
        # Проверяем есть ли пользователи и сессии
        if 'users' in tables:
            user_count = session.execute(text("SELECT COUNT(*) FROM users")).scalar()
            print(f"👥 Пользователей зарегистрировано: {user_count}")
            
        if 'quiz_sessions' in tables:
            session_count = session.execute(text("SELECT COUNT(*) FROM quiz_sessions")).scalar()
            print(f"🎯 Сессий викторины: {session_count}")
        
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")
    finally:
        session.close()
        engine.dispose()

if __name__ == "__main__":
    check_tests()