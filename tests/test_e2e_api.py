import os
import json
import time
import threading

import requests
import uvicorn

from app.api.main import app
from app.core.database import create_tables

API_BASE = "http://127.0.0.1:5001"


def run_server():
    uvicorn.run(app, host="127.0.0.1", port=5001, log_level="error")


def setup_module(module):
    # Ensure DB tables exist
    create_tables()
    # Start API in background thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    # Wait server
    for _ in range(50):
        try:
            r = requests.get(f"{API_BASE}/")
            if r.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(0.1)


def test_full_flow():
    admin_key = os.getenv("ADMIN_API_KEY", "admin_secret_key_123")

    # 1) Создать тест
    resp = requests.post(
        f"{API_BASE}/admin/tests",
        headers={"X-API-Key": admin_key},
        json={"name": "E2E", "description": "e2e"},
    )
    assert resp.status_code == 200
    test_id = resp.json()["id"]

    # 2) Импортировать вопросы (1 вопрос)
    question = {
        "ID вопроса": "E2EQ1",
        "Формулировка вопроса": "Q?",
        "Текст вопроса": "T",
        "Ответы": [
            {"ID ответа": "E2EO1", "Текст ответа": "A", "Правильный-неправильный ответ": True, "Комментарий к ответу": "C"},
            {"ID ответа": "E2EO2", "Текст ответа": "B", "Правильный-неправильный ответ": False, "Комментарий к ответу": "C"},
        ],
    }
    resp = requests.post(
        f"{API_BASE}/admin/tests/{test_id}/questions/import",
        headers={"X-API-Key": admin_key, "Content-Type": "application/json"},
        json=[question],
    )
    assert resp.status_code == 200

    # 3) Регистрация пользователя
    resp = requests.post(
        f"{API_BASE}/public/users/register",
        json={"telegram_id": 123456, "first_name": "Test", "last_name": "User"},
    )
    assert resp.status_code == 200

    # 4) Старт сессии
    resp = requests.post(
        f"{API_BASE}/public/sessions/start",
        json={"telegram_id": 123456, "test_id": test_id, "shuffle": False},
    )
    assert resp.status_code == 200
    session_id = resp.json()["session_id"]

    # 5) Получить следующий вопрос
    resp = requests.get(f"{API_BASE}/public/sessions/{session_id}/next")
    assert resp.status_code == 200
    q = resp.json()
    assert q["question_id"] == "E2EQ1"

    # 6) Ответить правильно
    resp = requests.post(
        f"{API_BASE}/public/sessions/{session_id}/answer",
        json={"option_id": "E2EO1"},
    )
    assert resp.status_code == 200
    assert resp.json()["is_correct"] is True

    # 7) Завершить сессию
    resp = requests.post(f"{API_BASE}/public/sessions/{session_id}/finish")
    assert resp.status_code == 200
    body = resp.json()
    assert body["correct_count"] == 1
    assert body["total_count"] == 1


