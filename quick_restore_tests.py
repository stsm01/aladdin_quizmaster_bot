#!/usr/bin/env python3
"""
Быстрое восстановление тестов из бэкапа
Используйте этот скрипт если тесты пропали после деплоя
"""

import json
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def restore_from_backup():
    """Восстановить тесты из последнего бэкапа"""
    
    # Найти последний бэкап
    import glob
    backup_files = glob.glob("tests_backup_*.json")
    if not backup_files:
        print("❌ Бэкап файлы не найдены!")
        return
    
    latest_backup = max(backup_files)
    print(f"📁 Используем бэкап: {latest_backup}")
    
    # Загрузить данные из бэкапа
    with open(latest_backup, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"📊 В бэкапе найдено:")
    print(f"   📋 Тестов: {len(data['tests'])}")
    print(f"   ❓ Вопросов: {len(data['questions'])}")
    print(f"   🔘 Вариантов: {len(data['answer_options'])}")
    
    # Подключение к базе
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        print("🔄 Очищаем и восстанавливаем данные...")
        
        # Очищаем таблицы в правильном порядке (из-за foreign keys)
        session.execute(text("DELETE FROM answer_options"))
        session.execute(text("DELETE FROM questions"))  
        session.execute(text("DELETE FROM tests"))
        session.commit()
        print("   🗑️  Старые данные удалены")
        
        # Восстанавливаем тесты
        for test in data["tests"]:
            session.execute(text("""
                INSERT INTO tests (id, name, description, created_at) 
                VALUES (:id, :name, :description, :created_at)
            """), test)
        print(f"   ✅ Восстановлено {len(data['tests'])} тестов")
        
        # Восстанавливаем вопросы
        for question in data["questions"]:
            session.execute(text("""
                INSERT INTO questions (id, test_id, title, text, created_at) 
                VALUES (:id, :test_id, :title, :text, :created_at)
            """), question)
        print(f"   ✅ Восстановлено {len(data['questions'])} вопросов")
        
        # Восстанавливаем варианты ответов
        for option in data["answer_options"]:
            session.execute(text("""
                INSERT INTO answer_options (id, question_id, text, is_correct, comment) 
                VALUES (:id, :question_id, :text, :is_correct, :comment)
            """), option)
        print(f"   ✅ Восстановлено {len(data['answer_options'])} вариантов ответов")
        
        session.commit()
        
        # Проверка
        test_count = session.execute(text("SELECT COUNT(*) FROM tests")).scalar()
        question_count = session.execute(text("SELECT COUNT(*) FROM questions")).scalar()
        option_count = session.execute(text("SELECT COUNT(*) FROM answer_options")).scalar()
        
        print("🎉 Восстановление завершено!")
        print(f"📊 Итого в базе:")
        print(f"   📋 Тестов: {test_count}")
        print(f"   ❓ Вопросов: {question_count}")
        print(f"   🔘 Вариантов: {option_count}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Ошибка восстановления: {e}")
        raise
    finally:
        session.close()
        engine.dispose()

def check_current_state():
    """Проверить текущее состояние базы"""
    DATABASE_URL = os.getenv("DATABASE_URL")
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        test_count = session.execute(text("SELECT COUNT(*) FROM tests")).scalar()
        question_count = session.execute(text("SELECT COUNT(*) FROM questions")).scalar()
        option_count = session.execute(text("SELECT COUNT(*) FROM answer_options")).scalar()
        
        print("📊 Текущее состояние базы:")
        print(f"   📋 Тестов: {test_count}")
        print(f"   ❓ Вопросов: {question_count}") 
        print(f"   🔘 Вариантов: {option_count}")
        
        if test_count > 0:
            tests = session.execute(text("SELECT name FROM tests")).fetchall()
            print("📋 Существующие тесты:")
            for test in tests:
                print(f"   - {test[0]}")
        else:
            print("⚠️  Тесты не найдены!")
            
    finally:
        session.close()
        engine.dispose()

if __name__ == "__main__":
    print("🔍 Проверяем текущее состояние...")
    check_current_state()
    
    print("\n" + "="*50)
    response = input("Нужно восстановить тесты из бэкапа? (y/N): ")
    
    if response.lower() in ['y', 'yes', 'да', 'д']:
        print("🚀 Начинаем восстановление...")
        restore_from_backup()
    else:
        print("✋ Восстановление отменено")