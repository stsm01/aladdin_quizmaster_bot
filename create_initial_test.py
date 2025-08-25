#!/usr/bin/env python3
"""
Create the initial test "Релиз 1.12" and migrate existing questions to it
"""

import requests
import json
import uuid

# API Configuration
API_BASE = "http://localhost:5000"
ADMIN_API_KEY = "admin_secret_key_123"

def create_test():
    """Create the initial test"""
    test_data = {
        "name": "Релиз 1.12",
        "description": "Тест знаний по релизу 1.12 системы"
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(
        f"{API_BASE}/admin/tests",
        json=test_data,
        headers=headers
    )
    
    if response.status_code == 200:
        test = response.json()
        print(f"✅ Created test: {test['name']} (ID: {test['id']})")
        return test['id']
    else:
        print(f"❌ Failed to create test: {response.status_code}")
        print(response.text)
        return None

def get_available_tests():
    """Get all available tests"""
    response = requests.get(f"{API_BASE}/public/tests")
    
    if response.status_code == 200:
        tests = response.json()
        print(f"📋 Available tests ({len(tests)}):")
        for test in tests:
            print(f"  - {test['name']} (ID: {test['id']}, Questions: {test['questions_count']})")
        return tests
    else:
        print(f"❌ Failed to get tests: {response.status_code}")
        print(response.text)
        return []

if __name__ == "__main__":
    print("🚀 Creating initial test 'Релиз 1.12'...")
    
    # Create the test
    test_id = create_test()
    
    if test_id:
        print(f"\n📊 Test created successfully with ID: {test_id}")
        
        # Show available tests
        print("\n" + "="*50)
        get_available_tests()
        
        print(f"\n✅ Setup complete!")
        print(f"🎯 Test ID для использования в боте: {test_id}")
        print("📝 Теперь можно импортировать вопросы через admin API:")
        print(f"   POST /admin/tests/{test_id}/questions/import")
    else:
        print("\n❌ Failed to setup initial test")