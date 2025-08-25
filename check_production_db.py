#!/usr/bin/env python3
"""
Проверка состояния ПРОДОВОЙ базы данных
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# URL продовой базы
PROD_DATABASE_URL = "postgresql://neondb_owner:npg_9BH3JEMRwQna@ep-bitter-lake-a69kivks.us-west-2.aws.neon.tech/neondb?sslmode=require"

def check_production_db():
    """Проверить состояние продовой базы данных"""
    print("🏭 ПРОВЕРКА ПРОДОВОЙ БАЗЫ ДАННЫХ")
    print("=" * 50)
    print(f"🔗 URL: ep-bitter-lake-a69kivks.us-west-2.aws.neon.tech")
    print()
    
    try:
        engine = create_engine(PROD_DATABASE_URL, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        session = SessionLocal()
        
        # Проверяем существование таблиц
        tables_result = session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        tables = [row[0] for row in tables_result]
        print(f"📋 Таблицы в продовой базе: {', '.join(tables) if tables else 'НЕТ ТАБЛИЦ'}")
        print()
        
        if not tables:
            print("❌ Продовая база пустая! Таблицы не созданы.")
            return
            
        if 'tests' not in tables:
            print("❌ Таблица 'tests' не найдена в продовой базе!")
            return
            
        # Считаем записи
        test_count = session.execute(text("SELECT COUNT(*) FROM tests")).scalar()
        question_count = session.execute(text("SELECT COUNT(*) FROM questions")).scalar() if 'questions' in tables else 0
        option_count = session.execute(text("SELECT COUNT(*) FROM answer_options")).scalar() if 'answer_options' in tables else 0
        
        print("📊 СОСТОЯНИЕ ПРОДОВОЙ БАЗЫ:")
        print(f"   📋 Тестов: {test_count}")
        print(f"   ❓ Вопросов: {question_count}")
        print(f"   🔘 Вариантов ответов: {option_count}")
        print()
        
        if test_count > 0:
            print("📝 ТЕСТЫ В ПРОДОВОЙ БАЗЕ:")
            tests_result = session.execute(text("""
                SELECT t.id, t.name, t.description, COUNT(q.id) as questions_count 
                FROM tests t 
                LEFT JOIN questions q ON t.id = q.test_id 
                GROUP BY t.id, t.name, t.description 
                ORDER BY t.created_at
            """))
            
            for i, test in enumerate(tests_result, 1):
                print(f"   {i}. 📋 {test[1]}")
                print(f"      📄 {test[2]}")
                print(f"      ❓ Вопросов: {test[3]}")
                print(f"      🆔 ID: {test[0]}")
                print()
                
            print("🎉 ПРОДОВАЯ БАЗА ГОТОВА К РАБОТЕ!")
                
        else:
            print("⚠️  ВНИМАНИЕ: В продовой базе НЕТ ТЕСТОВ!")
            print("💡 Запустите: python transfer_to_production.py")
        
        # Дополнительные проверки
        if 'users' in tables:
            user_count = session.execute(text("SELECT COUNT(*) FROM users")).scalar()
            print(f"👥 Пользователей в продовой базе: {user_count}")
            
        if 'quiz_sessions' in tables:
            session_count = session.execute(text("SELECT COUNT(*) FROM quiz_sessions")).scalar()
            print(f"🎯 Сессий викторины в продовой базе: {session_count}")
        
        session.close()
        engine.dispose()
        
    except Exception as e:
        print(f"❌ ОШИБКА подключения к продовой базе: {e}")
        print()
        print("Возможные причины:")
        print("1. Неверные учетные данные")
        print("2. База данных недоступна")
        print("3. Проблемы с SSL подключением")

if __name__ == "__main__":
    check_production_db()